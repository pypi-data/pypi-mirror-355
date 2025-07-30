import math
from numpy.typing import NDArray


class GlobalBase:
    def matrix(self, query_sequence: str, subject_sequence: str) -> list[list[float]]:
        matrix, _ = self(query_sequence, subject_sequence)
        return matrix

    def distance(self, query_sequence: str, subject_sequence: str) -> float:
        if not query_sequence and not subject_sequence:
            return 0.0
        if not query_sequence or not subject_sequence:
            return float(len(query_sequence or subject_sequence)) * self.gap_penalty

        raw_sim = self.similarity(query_sequence, subject_sequence)
        max_possible = (
            max(len(query_sequence), len(subject_sequence)) * self.match_score
        )
        return max_possible - abs(raw_sim)

    def similarity(self, query_sequence: str, subject_sequence: str) -> float:
        if not query_sequence and not subject_sequence:
            return 1.0
        matrix, _ = self(query_sequence, subject_sequence)
        return matrix[matrix.shape[0] - 1, matrix.shape[1] - 1]

    def normalized_distance(self, query_sequence: str, subject_sequence: str) -> float:
        return 1 - self.normalized_similarity(query_sequence, subject_sequence)

    def normalized_similarity(
        self, query_sequence: str, subject_sequence: str
    ) -> float:
        raw_score = self.similarity(query_sequence, subject_sequence)
        max_len = len(max(query_sequence, subject_sequence, key=len))
        max_possible = max_len * self.match_score
        min_possible = -max_len * self.mismatch_penalty
        score_range = max_possible - min_possible
        return (raw_score - min_possible) / score_range

    def align(self, query_sequence: str, subject_sequence: str) -> str:
        _, pointer_matrix = self(query_sequence, subject_sequence)

        qs = [x.upper() for x in query_sequence]
        ss = [x.upper() for x in subject_sequence]
        i, j = len(qs), len(ss)
        query_align, subject_align = [], []

        # looks for match/mismatch/gap starting from bottom right of matrix
        while i > 0 or j > 0:
            if pointer_matrix[i, j] in [2, 5, 6, 9]:
                # appends match/mismatch then moves to the cell diagonally up and to the left
                query_align.append(qs[i - 1])
                subject_align.append(ss[j - 1])
                i -= 1
                j -= 1
            elif pointer_matrix[i, j] in [3, 5, 7, 9]:
                # appends gap and accompanying nucleotide, then moves to the cell above
                subject_align.append("-")
                query_align.append(qs[i - 1])
                i -= 1
            elif pointer_matrix[i, j] in [4, 6, 7, 9]:
                # appends gap and accompanying nucleotide, then moves to the cell to the left
                subject_align.append(ss[j - 1])
                query_align.append("-")
                j -= 1

        query_align = "".join(query_align[::-1])
        subject_align = "".join(subject_align[::-1])

        return f"{query_align}\n{subject_align}"


class LocalBase:
    def matrix(self, query_sequence: str, subject_sequence: str) -> NDArray:
        """Return alignment matrix"""
        matrix = self(query_sequence, subject_sequence)
        return matrix

    def similarity(self, query_sequence: str, subject_sequence: str) -> float:
        """Calculate similarity score"""
        matrix = self(query_sequence, subject_sequence)
        return matrix.max() if matrix.max() > 1 else 0.0

    def distance(self, query_sequence: str, subject_sequence: str) -> float:
        """Calculate a proper metric distance based on local alignment score.

        Uses the formula: d(x,y) = -ln(sim_AB / sqrt(sim_A * sim_B))
        This ensures the triangle inequality property.
        """
        query_length = len(query_sequence)
        subject_length = len(subject_sequence)
        if not query_sequence and not subject_sequence:
            return 0.0
        if not query_sequence or not subject_sequence:
            return max(query_length, subject_length)

        sim_A = query_length
        sim_B = subject_length
        matrix = self(query_sequence, subject_sequence)
        sim_AB = matrix.max()

        if sim_AB == 0:
            return max(query_length, subject_length)
        return -math.log(sim_AB / math.sqrt(sim_A * sim_B))

    def normalized_similarity(
        self, query_sequence: str, subject_sequence: str
    ) -> float:
        """Calculate normalized similarity between 0 and 1"""
        if not query_sequence and not subject_sequence:
            return 1.0
        if not query_sequence or not subject_sequence:
            return 0.0
        matrix = self(query_sequence, subject_sequence)
        best_score = matrix.max()
        return best_score / min(len(query_sequence), len(subject_sequence))

    def normalized_distance(self, query_sequence: str, subject_sequence: str) -> float:
        """Calculate normalized distance between 0 and 1"""
        if not query_sequence and not subject_sequence:
            return 0.0
        if not query_sequence or not subject_sequence:
            return 1.0
        return 1.0 - self.normalized_similarity(query_sequence, subject_sequence)
