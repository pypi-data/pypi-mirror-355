import asyncio
import copy
import os
import time
from typing import Dict, List, Optional

# Import necessary types
from ragchat.definitions import BatchStatusSummary, FileState, FileStatus
from ragchat.log import get_logger

logger = get_logger(__name__)


class BatchProgress:
    """
    Tracks and manages the progress of a batch of files being processed.
    Provides methods to update file states, calculate overall progress,
    and format progress information for display.
    """

    def __init__(
        self, total_files: int, total_batch_bytes_expected: Optional[float] = None
    ):
        """
        Initializes the BatchProgress tracker.

        Args:
            total_files: The total number of files in the batch.
            total_batch_bytes_expected: The expected total size of the batch in bytes, if known.
        """
        self.total_files = total_files
        self.file_states: Dict[str, FileState] = {}
        self._lock = asyncio.Lock()
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
        self.total_batch_bytes: Optional[float] = total_batch_bytes_expected
        self._last_yielded_percentage: float = -1.0
        self._last_progress_summary: Optional[BatchStatusSummary] = None
        self._last_progress_summary_had_files: bool = False

    async def handle_file_state(self, file_state: FileState) -> None:
        """
        Updates the state of a single file within the batch.
        Automatically starts and ends the batch timer based on file states.

        Args:
            file_state: The updated state of a file.
        """
        async with self._lock:
            task_id = file_state.task_id
            if task_id is None:
                return

            self.file_states[task_id] = file_state

            if self._start_time is None:
                self._start_time = time.time()

            files_done_count = sum(
                1 for f in self.file_states.values() if f.is_terminal
            )
            if (
                files_done_count == self.total_files
                and self.total_files > 0
                and self._end_time is None
            ):
                self._end_time = time.time()

    def _get_status_summary_unlocked(self) -> BatchStatusSummary:
        """
        Calculates and returns the current status summary of the batch.
        This method is not thread-safe and should only be called from within a locked context.

        Returns:
            A BatchStatusSummary object containing the current progress.
        """
        current_time = time.time()
        elapsed_time = current_time - self._start_time if self._start_time else 0.0
        all_states = list(self.file_states.values())

        processed_batch_bytes = sum(
            s.processed_bytes for s in all_states if s.processed_bytes is not None
        )
        current_percentage = 0.0
        remaining_time: Optional[float] = None

        if self.total_batch_bytes is not None:
            if self.total_batch_bytes > 0:
                current_percentage = (
                    processed_batch_bytes / self.total_batch_bytes
                ) * 100.0
                if elapsed_time > 0 and processed_batch_bytes > 0:
                    bytes_per_second = processed_batch_bytes / elapsed_time
                    remaining_bytes = self.total_batch_bytes - processed_batch_bytes
                    if remaining_bytes > 0:
                        remaining_time = (
                            remaining_bytes / bytes_per_second
                            if bytes_per_second > 0
                            else None
                        )
                    else:
                        remaining_time = 0.0
            elif self.total_batch_bytes == 0 and self.total_files >= 0:
                current_percentage = 100.0
                remaining_time = 0.0
        else:
            known_chunk_states = [s for s in all_states if s.total_chunks is not None]
            total_known_chunks = sum(s.total_chunks or 0 for s in known_chunk_states)
            processed_chunks = sum(len(s.chunk_results) for s in all_states)

            avg_chunks_per_file = (
                (total_known_chunks / len(known_chunk_states))
                if len(known_chunk_states) > 0
                else 0
            )
            files_without_known_chunks = self.total_files - len(known_chunk_states)
            avg_chunks_per_file = max(0, avg_chunks_per_file)
            total_chunks_est = (
                total_known_chunks + files_without_known_chunks * avg_chunks_per_file
            )

            if total_chunks_est > 0:
                current_percentage = (processed_chunks / total_chunks_est) * 100.0
                if processed_chunks > 0 and elapsed_time > 0:
                    chunks_per_second = processed_chunks / elapsed_time
                    remaining_chunks = total_chunks_est - processed_chunks
                    if remaining_chunks > 0:
                        remaining_time = (
                            remaining_chunks / chunks_per_second
                            if chunks_per_second > 0
                            else None
                        )
                    else:
                        remaining_time = 0.0
            elif self.total_files > 0:
                files_done_count = sum(1 for s in all_states if s.is_terminal)
                current_percentage = (files_done_count / self.total_files) * 100.0
                if 0 < files_done_count < self.total_files and elapsed_time > 0:
                    time_per_file = elapsed_time / files_done_count
                    remaining_time = (
                        self.total_files - files_done_count
                    ) * time_per_file
                elif files_done_count == self.total_files:
                    remaining_time = 0.0

        if self.total_files == 0:
            current_percentage = 100.0
            remaining_time = 0.0

        if (
            sum(1 for s in all_states if s.is_terminal) == self.total_files
            and self.total_files > 0
        ):
            current_percentage = 100.0
            remaining_time = 0.0
            if self._end_time and self._start_time:
                elapsed_time = self._end_time - self._start_time

        current_percentage = min(100.0, max(0.0, current_percentage))

        return BatchStatusSummary(
            total_files=self.total_files,
            files_done=sum(1 for s in all_states if s.is_terminal),
            processing_files=sum(
                1 for s in all_states if s.status == FileStatus.PROCESSING
            ),
            percentage=round(current_percentage, 2),
            elapsed_time=round(elapsed_time, 2),
            remaining_time=round(remaining_time, 2)
            if remaining_time is not None
            else None,
            file_states=copy.deepcopy(self.file_states),
            total_batch_bytes=self.total_batch_bytes,
            processed_batch_bytes=processed_batch_bytes,
        )

    async def get_status_summary(self) -> BatchStatusSummary:
        """
        Retrieves the current status summary of the batch in a thread-safe manner.

        Returns:
            A BatchStatusSummary object containing the current progress.
        """
        async with self._lock:
            return self._get_status_summary_unlocked()

    async def maybe_get_progress_update(
        self, with_files: bool = False
    ) -> Optional[str]:
        """
        Generates a formatted progress string if a significant change has occurred
        since the last update.

        Args:
            with_files: If True, includes detailed file progress in the output string.

        Returns:
            A formatted progress string if an update is needed, otherwise None.
        """
        async with self._lock:
            current_summary = self._get_status_summary_unlocked()
            current_percentage = current_summary.percentage

            yield_needed = False
            if self._last_progress_summary is None:
                yield_needed = True
            else:
                if (
                    current_summary.files_done > self._last_progress_summary.files_done
                    or current_summary.processing_files
                    != self._last_progress_summary.processing_files
                ):
                    yield_needed = True
                elif (
                    current_percentage >= 100.0
                    and self._last_progress_summary.percentage < 100.0
                ):
                    yield_needed = True
                elif (
                    current_percentage >= 100.0
                    and self._last_progress_summary.percentage >= 100.0
                    and with_files
                    and not self._last_progress_summary_had_files
                ):
                    yield_needed = True
                elif (
                    current_percentage < 100.0
                    and (current_percentage - self._last_yielded_percentage) >= 1.0
                ):
                    yield_needed = True

            if yield_needed:
                include_file_details = with_files or (
                    current_percentage >= 100.0
                    and (
                        self._last_progress_summary is None
                        or self._last_progress_summary.percentage < 100.0
                        or not self._last_progress_summary_had_files
                    )
                )

                chunk = self.format_progress_chunk(
                    current_summary, include_file_details
                )
                self._last_yielded_percentage = current_percentage
                self._last_progress_summary = current_summary
                self._last_progress_summary_had_files = include_file_details
                return chunk
            return None

    async def get_non_terminal_task_ids(self) -> List[str]:
        """
        Retrieves a list of task IDs for files that are not yet in a terminal state.

        Returns:
            A list of strings, where each string is a task ID.
        """
        async with self._lock:
            return [
                task_id
                for task_id, state in self.file_states.items()
                if not state.is_terminal
            ]

    def format_time(self, seconds: Optional[float]) -> str:
        """
        Formats a duration in seconds into a human-readable string (e.g., "1h 30m 5s").

        Args:
            seconds: The duration in seconds.

        Returns:
            A formatted time string.
        """
        if seconds is None or seconds < 0:
            return "N/A"
        if seconds == 0:
            return "0s"
        if seconds < 60:
            return f"{int(seconds)}s"
        if seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        return f"{int(seconds // 3600)}h {int((seconds % 3600) // 60)}m"

    def format_bytes(self, byte_count: Optional[float]) -> str:
        """
        Formats a byte count into a human-readable string (e.g., "1.23 MB").

        Args:
            byte_count: The number of bytes.

        Returns:
            A formatted byte size string, right-aligned to a fixed width.
        """
        TARGET_WIDTH = 9

        if byte_count is None or byte_count < 0:
            return "N/A".rjust(TARGET_WIDTH)

        if byte_count == 0:
            return "0.00 B".rjust(TARGET_WIDTH)

        size_name = ("B ", "KB", "MB", "GB", "TB")

        s = float(byte_count)
        i = 0

        while s >= 1000 and i < len(size_name) - 1:
            s /= 1024
            i += 1

        s = round(s, 2)

        formatted_string = f"{s:.2f} {size_name[i]}"

        return formatted_string.rjust(TARGET_WIDTH)

    def format_progress_chunk(
        self, summary: BatchStatusSummary, with_files: bool = False
    ) -> str:
        """
        Formats a BatchStatusSummary into a multi-line string suitable for display.

        Args:
            summary: The BatchStatusSummary object to format.
            with_files: If True, includes detailed file progress lines.

        Returns:
            A formatted string representing the batch progress.
        """
        lines = []
        self.format_bytes(summary.total_batch_bytes)
        self.format_bytes(summary.processed_batch_bytes)

        overall_progress_parts = [
            f"`{summary.percentage:3.0f}%",
            f"Files: {summary.files_done:>3}/{summary.total_files} done ({summary.processing_files} processing)",
            f"Time elapsed: {self.format_time(summary.elapsed_time):>8}",
        ]
        if summary.remaining_time is not None:
            overall_progress_parts.append(
                f"Remaining: {self.format_time(summary.remaining_time):>8}"
            )
        lines.append(" - ".join(overall_progress_parts) + "`")

        if with_files and summary.file_states:
            lines.append("\nFiles:")
            sorted_file_states = sorted(
                summary.file_states.values(), key=lambda x: x.file_path
            )
            for file_state in sorted_file_states:
                status_str = file_state.status.value
                successful_chunks = sum(not c.error for c in file_state.chunk_results)
                total_chunks_display = (
                    file_state.total_chunks
                    if file_state.total_chunks is not None
                    else "?"
                )

                file_total_bytes_display = self.format_bytes(file_state.total_bytes)
                file_processed_bytes_display = self.format_bytes(
                    file_state.processed_bytes
                )
                file_bytes_progress = (
                    f"{file_processed_bytes_display} / {file_total_bytes_display}"
                )

                file_line = f"`{status_str:<10} - {successful_chunks:>2}/{total_chunks_display:>2} chunks - {file_bytes_progress} - {os.path.basename(file_state.file_path)}`"
                if file_state.error:
                    truncated_error = (
                        file_state.error[:77] + "..."
                        if len(file_state.error) > 80
                        else file_state.error
                    )
                    file_line += f" (Error: {truncated_error})"
                lines.append(file_line)
        return "\n".join(lines)
