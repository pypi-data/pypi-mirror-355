"""
Search operations for the ApolloAgent.

This module contains functions for search operations like codebase search,
grep search, and file search.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

import asyncio
import os
import re
import fnmatch
import aiofiles
from typing import Dict, Any, AsyncGenerator, List
from thefuzz import fuzz
from typing import Protocol


class AgentWithWorkspace(Protocol):
    """
    Protocol for objects that are expected to have a workspace_path attribute.
    This defines the minimum interface required by search functions.
    """

    workspace_path: str


async def codebase_search(agent: AgentWithWorkspace, query: str) -> Dict[str, Any]:
    """
    Finds code snippets from the codebase most relevant to the search query.
    This function performs a keyword-based search by checking if all significant
    keywords from the query are present in the file content. This aims for better
    relevance than a simple substring match, as a step towards more advanced
    semantic search.

    Args:
        agent: An agent instance possessing a `workspace_path` attribute (str).
        query: The natural language search query.

    Returns:
        A dictionary containing the search query and a list of results.
        Each result includes the file path, a content snippet, and a relevance score.
        Returns an error structure if the workspace path is invalid.
    """
    results = []
    # Ensure the workspace path is absolute to handle relative paths correctly
    workspace_root_abs = os.path.abspath(agent.workspace_path)

    if not os.path.isdir(workspace_root_abs):
        # Log a warning and return an error if the workspace path is not a valid directory
        print(
            f"[WARNING] Workspace path is not a valid directory, skipping: {agent.workspace_path}"
        )
        return {
            "query": query,
            "results": [],
            "error": f"Workspace path '{agent.workspace_path}' is not a valid directory.",
        }

    # Define file extensions to be included in the search.
    included_extensions = (
        ".py",
        ".js",
        ".ts",
        ".html",
        ".css",
        ".java",
        ".c",
        ".cpp",
        ".txt",
        ".md",
    )

    # Optional: Define a limit for the number of results
    max_result = 20

    # Process the query to get keywords
    # Split by non-alphanumeric characters, convert to lower, filter short/common words
    # Basic stop words list; can be expanded or made more sophisticated
    basic_stop_words = {
        "the",
        "for",
        "and",
        "with",
        "this",
        "that",
        "how",
        "what",
        "why",
        "is",
        "in",
        "it",
        "of",
        "to",
        "a",
        "an",
    }
    query_keywords = [
        word
        for word in re.split(r"\W+", query.lower())
        if len(word) > 2 and word not in basic_stop_words
    ]

    # If after filtering, no meaningful keywords remain, we likely won't find good matches.
    # The 'all' logic below will handle this by not matching if query_keywords is empty.

    for root, _, files in os.walk(workspace_root_abs):
        for file_name in files:
            if file_name.endswith(included_extensions):
                file_path_abs = os.path.join(root, file_name)
                try:
                    async with aiofiles.open(
                        file_path_abs, "r", encoding="utf-8", errors="ignore"
                    ) as f:
                        content = await f.read()

                    content_lower = content.lower()
                    match_found = False

                    if query_keywords:  # Only proceed if we have keywords to search for
                        # Check if all processed keywords are present in the content
                        if all(keyword in content_lower for keyword in query_keywords):
                            match_found = True

                    if match_found:
                        relative_file_path: str = os.path.relpath(
                            file_path_abs, workspace_root_abs
                        )
                        results.append(
                            {
                                "file_path": relative_file_path,
                                "content_snippet": (
                                    content[:500] + "..."
                                    if len(content) > 500
                                    else content
                                ),
                                "relevance_score": 0.75,  # This is a placeholder, real relevance is complex
                            }
                        )
                        if len(results) >= max_result:
                            break  # Break from the inner files loop
                except OSError as e:
                    # Log OSError during file read and continue with other files
                    print(f"[ERROR] Error reading file {file_path_abs}: {e}")
                except RuntimeError as e:
                    # Log other unexpected errors during file processing and continue
                    print(
                        f"[ERROR] Unexpected error processing file {file_path_abs}: {e}"
                    )

            if len(results) >= max_result:  # Check after processing each file
                break  # Break from the inner files loop if limit reached

        if (
            len(results) >= max_result
        ):  # Check after processing all files in a directory
            break  # Break from the outer os.walk loop if limit reached

    return {"query": query, "results": results}


def match_pattern_sync(filename: str, pattern: str) -> bool:
    """
    Synchronous check if a filename matches a glob pattern.

    Args:
        filename: The filename to check.
        pattern: The glob pattern to match against.

    Returns:
        True if the filename matches the pattern, False otherwise.
    """
    return fnmatch.fnmatch(filename, pattern)


async def _walk_files_async(dir_path: str) -> AsyncGenerator[str, None]:
    """
    Asynchronously generates file paths from a directory tree.
    Wraps os.walk in an executor to make it non-blocking.
    Note: This version collects all paths first in the executor, then yields.
    For extremely large directory trees, a more advanced streaming approach
    (e.g., using an asyncio.Queue with a producer thread) would be more memory-efficient.
    """
    loop = asyncio.get_running_loop()

    def _synchronous_walk():
        paths = []
        for root_dir, _, files_in_dir in os.walk(dir_path):
            for file_name in files_in_dir:
                paths.append(os.path.join(root_dir, file_name))
        return paths

    try:
        file_paths = await loop.run_in_executor(None, _synchronous_walk)
        for path in file_paths:
            yield path
    except RuntimeError:
        # If os.walk itself fails (e.g., the path doesn't exist, permissions),
        # this generator will stop. Errors during a walk can be logged here if needed.
        # The main function will then have no files to process from this generator.
        return


async def grep_search(
    agent: Any,
    query: str,
    max_results: int = 50,
    regex_flags: int = 0,
) -> Dict[str, Any]:
    """
    Asynchronously searches for a regex pattern within files in a directory.
    Best for finding specific strings or patterns.

    Args:
        agent: An object with a `workspace_path` string attribute.
        query: The regex pattern to search for.
        max_results: The maximum number of results to return.
        regex_flags: Flags for the regex search (e.g., re.IGNORECASE).

    Returns:
        Dictionary with search results, including any errors encountered.
    """
    results: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []

    if not hasattr(agent, "workspace_path") or not isinstance(
        agent.workspace_path, str
    ):
        return {
            "query": query,
            "results": [],
            "total_matches_found": 0,
            "capped": False,
            "errors": [
                {"file": "N/A", "error": "Agent has no valid workspace_path attribute."}
            ],
        }

    try:
        compiled_regex = re.compile(query, flags=regex_flags)
    except re.error as e:
        return {
            "query": query,
            "results": [],
            "total_matches_found": 0,
            "capped": False,
            "errors": [{"file": "N/A", "error": f"Invalid regex pattern: {e}"}],
        }

    async for file_path_str in _walk_files_async(agent.workspace_path):
        if len(results) >= max_results:
            break

        relative_file_path = os.path.relpath(file_path_str, agent.workspace_path)
        try:
            async with aiofiles.open(
                file_path_str, "r", encoding="utf-8", errors="ignore"
            ) as f:
                line_number = 0
                async for line in f:
                    line_number += 1
                    if len(results) >= max_results:
                        break

                    match = await asyncio.to_thread(compiled_regex.search, line)
                    if match:
                        results.append(
                            {
                                "file": relative_file_path,
                                "line_number": line_number,
                                "content": line.strip(),
                            }
                        )
                        if len(results) >= max_results:
                            break
        except OSError as e:
            errors.append({"file": relative_file_path, "error": f"OSError: {e}"})
        except RuntimeError as e:
            errors.append(
                {"file": relative_file_path, "error": f"Unexpected error: {e}"}
            )

        if len(results) >= max_results:
            break

    return {
        "query": query,
        "results": results,
        "total_matches_found": len(results),
        "capped": len(results) >= max_results,
        "errors": errors,
    }


async def file_search(
    agent: AgentWithWorkspace, query: str, threshold: int = 75, max_results: int = 10
) -> Dict[str, Any]:
    """
    Fast file search based on fuzzy matching against a file path.
    Uses the `thefuzz` library to find files with similar names to the query.

    Args:
        agent: Apollo agent instance with a `workspace_path` attribute.
        query: The filename or part of a filename to search for (fuzzy).
        threshold: The minimum similarity score (0-100) for a match.
                   Defaults to 75.
        max_results: The maximum number of results to return.
        Default to 10.


    Returns:
        Dictionary with search results, including total matches and if results were capped.
    """
    results = []
    query_lower = query.lower()

    # Iterate over files in the workspace
    for root, _, files in os.walk(agent.workspace_path):
        for file_name in files:
            file_name_lower = file_name.lower()
            score = fuzz.partial_ratio(query_lower, file_name_lower)

            if score >= threshold:
                # If the score is above the threshold, consider it a match
                full_file_path = os.path.join(root, file_name)
                relative_file_path = os.path.relpath(
                    full_file_path, agent.workspace_path
                )
                results.append(
                    {
                        "file_path": relative_file_path,
                        "filename": file_name,
                        "similarity_score": score,
                    }
                )

                if len(results) >= max_results:
                    break

        if len(results) >= max_results:
            break

    return {
        "query": query,
        "results": results,
        "total_matches": len(results),
        "capped": len(results) >= max_results,
    }
