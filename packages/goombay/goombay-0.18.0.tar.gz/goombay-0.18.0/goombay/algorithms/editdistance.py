# built-ins
import math

# internal dependencies
from goombay.algorithms.base import GlobalBase as _GlobalBase, LocalBase as _LocalBase

try:
    # external dependencies
    import numpy
    from numpy import float64
    from numpy._typing import NDArray
except ImportError:
    raise ImportError("Please pip install all dependencies from requirements.txt!")


def main():
    """
    qqs = "HOLYWATERISABLESSING"
    sss = ["HOLYWATERBLESSING", "HOLYERISSING", "HOLYWATISSSI", "HWATISBLESSING", "HOLYWATISSS"]

    for i in range(len(sss)):
        print(waterman_smith_beyer.align(qqs, sss[i]))
        print()
    print(waterman_smith_beyer.matrix("TRATE", "TRACE"))
    """
    query = "AGTC"
    subject = "AGGCAT"
    print(longest_common_substring.distance(query, subject))
    print(longest_common_subsequence.distance(query, subject))
    print(longest_common_substring.similarity(query, subject))
    print(longest_common_substring.normalized_similarity(query, subject))
    print(longest_common_substring.normalized_distance(query, subject))
    print(longest_common_subsequence.matrix(query, subject))
    print(longest_common_substring.align(query, subject))
    print(longest_common_subsequence.align(query, subject))


class WagnerFischer(_GlobalBase):  # Levenshtein Distance
    def __init__(self) -> None:
        self.gap_penalty = 1
        self.substitution_cost = 1

    def __call__(
        self, query_sequence: str, subject_sequence: str
    ) -> tuple[NDArray[float64], NDArray[float64]]:
        qs, ss = [""], [""]
        qs.extend([x.upper() for x in query_sequence])
        ss.extend([x.upper() for x in subject_sequence])

        # matrix initialisation
        self.alignment_score = numpy.zeros((len(qs), len(ss)))
        # pointer matrix to trace optimal alignment
        self.pointer = numpy.zeros((len(qs), len(ss)))
        self.pointer[:, 0] = 3
        self.pointer[0, :] = 4
        # initialisation of starter values for first column and first row
        self.alignment_score[:, 0] = [n for n in range(len(qs))]
        self.alignment_score[0, :] = [n for n in range(len(ss))]

        for i in range(1, len(qs)):
            for j in range(1, len(ss)):
                substitution_cost = 0
                if qs[i] != ss[j]:
                    substitution_cost = self.substitution_cost
                match = self.alignment_score[i - 1][j - 1] + substitution_cost
                ugap = self.alignment_score[i - 1][j] + self.gap_penalty
                lgap = self.alignment_score[i][j - 1] + self.gap_penalty

                tmin = min(match, lgap, ugap)

                self.alignment_score[i][j] = tmin  # lowest value is best choice
                # matrix for traceback based on results from scoring matrix
                if match == tmin:
                    self.pointer[i, j] += 2
                if ugap == tmin:
                    self.pointer[i, j] += 3
                if lgap == tmin:
                    self.pointer[i, j] += 4
        return self.alignment_score, self.pointer

    def distance(self, query_sequence: str, subject_sequence: str) -> float:
        matrix, _ = self(query_sequence, subject_sequence)
        return float(matrix[-1, -1])

    def similarity(self, query_sequence: str, subject_sequence: str) -> float:
        if not query_sequence and not subject_sequence:
            return 1.0
        sim = max(len(query_sequence), len(subject_sequence)) - self.distance(
            query_sequence, subject_sequence
        )
        return max(0, sim)

    def normalized_distance(self, query_sequence: str, subject_sequence: str) -> float:
        if not query_sequence and not subject_sequence:
            return 0.0
        if not query_sequence or not subject_sequence:
            return 1.0
        max_len = max(len(str(query_sequence)), len(str(subject_sequence)))
        max_dist = max_len
        return self.distance(query_sequence, subject_sequence) / max_dist

    def normalized_similarity(
        self, query_sequence: str, subject_sequence: str
    ) -> float:
        return 1.0 - self.normalized_distance(query_sequence, subject_sequence)

    def matrix(self, query_sequence: str, subject_sequence: str) -> list[list[float]]:
        return super().matrix(query_sequence, subject_sequence)

    def align(self, query_sequence: str, subject_sequence: str) -> str:
        _, pointer_matrix = self(query_sequence, subject_sequence)

        qs, ss = [x.upper() for x in query_sequence], [
            x.upper() for x in subject_sequence
        ]
        i, j = len(qs), len(ss)
        query_align, subject_align = [], []
        # looks for match/mismatch/gap starting from bottom right of matrix
        while i > 0 or j > 0:
            if pointer_matrix[i, j] in [2, 5, 6, 10, 9, 13, 14, 17]:
                # appends match/mismatch then moves to the cell diagonally up and to the left
                query_align.append(qs[i - 1])
                subject_align.append(ss[j - 1])
                i -= 1
                j -= 1
            elif pointer_matrix[i, j] in [3, 5, 7, 11, 9, 13, 15, 17]:
                # appends gap and accompanying nucleotide, then moves to the cell above
                subject_align.append("-")
                query_align.append(qs[i - 1])
                i -= 1
            elif pointer_matrix[i, j] in [4, 6, 7, 12, 9, 14, 15, 17]:
                # appends gap and accompanying nucleotide, then moves to the cell to the left
                subject_align.append(ss[j - 1])
                query_align.append("-")
                j -= 1

        query_align = "".join(query_align[::-1])
        subject_align = "".join(subject_align[::-1])
        return f"{query_align}\n{subject_align}"


class LowranceWagner(_GlobalBase):  # Damerau-Levenshtein distance
    def __init__(self) -> None:
        self.gap_penalty = 1
        self.substitution_cost = 1
        self.transposition_cost = 1

    def __call__(
        self, query_sequence: str, subject_sequence: str
    ) -> tuple[NDArray[float64], NDArray[float64]]:
        qs, ss = [""], [""]
        qs.extend([x.upper() for x in query_sequence])
        ss.extend([x.upper() for x in subject_sequence])
        qs_len = len(qs)
        ss_len = len(ss)

        # matrix initialisation
        self.alignment_score = numpy.zeros((qs_len, ss_len))
        # pointer matrix to trace optimal alignment
        self.pointer = numpy.zeros((qs_len, ss_len))
        self.pointer[:, 0] = 3
        self.pointer[0, :] = 4
        # initialisation of starter values for first column and first row
        self.alignment_score[:, 0] = [n for n in range(qs_len)]
        self.alignment_score[0, :] = [n for n in range(ss_len)]

        for i in range(1, qs_len):
            for j in range(1, ss_len):
                substitution_cost = 0
                if qs[i] != ss[j]:
                    substitution_cost = self.substitution_cost
                match = self.alignment_score[i - 1][j - 1] + substitution_cost
                ugap = self.alignment_score[i - 1][j] + self.gap_penalty
                lgap = self.alignment_score[i][j - 1] + self.gap_penalty
                trans = (
                    self.alignment_score[i - 2][j - 2] + 1
                    if qs[i] == ss[j - 1] and ss[j] == qs[i - 1]
                    else float("inf")
                )
                tmin = min(match, lgap, ugap, trans)

                self.alignment_score[i][j] = tmin  # lowest value is best choice
                # matrix for traceback based on results from scoring matrix
                if match == tmin:
                    self.pointer[i, j] += 2
                if ugap == tmin:
                    self.pointer[i, j] += 3
                if lgap == tmin:
                    self.pointer[i, j] += 4
                if trans == tmin:
                    self.pointer[i, j] += 8
        return self.alignment_score, self.pointer

    def distance(self, query_sequence: str, subject_sequence: str) -> float:
        matrix, _ = self(query_sequence, subject_sequence)
        return float(matrix[-1, -1])

    def similarity(self, query_sequence: str, subject_sequence: str) -> float:
        if not query_sequence and not subject_sequence:
            return 1.0
        sim = max(len(query_sequence), len(subject_sequence)) - self.distance(
            query_sequence, subject_sequence
        )
        return max(0, sim)

    def normalized_distance(self, query_sequence: str, subject_sequence: str) -> float:
        if not query_sequence and not subject_sequence:
            return 0.0
        if not query_sequence or not subject_sequence:
            return 1.0
        max_len = max(len(str(query_sequence)), len(str(subject_sequence)))
        max_dist = max_len
        return self.distance(query_sequence, subject_sequence) / max_dist

    def normalized_similarity(
        self, query_sequence: str, subject_sequence: str
    ) -> float:
        return 1.0 - self.normalized_distance(query_sequence, subject_sequence)

    def matrix(self, query_sequence: str, subject_sequence: str) -> list[list[float]]:
        return super().matrix(query_sequence, subject_sequence)

    def align(self, query_sequence: str, subject_sequence: str) -> str:
        if not query_sequence and not subject_sequence:
            return "\n"
        if not query_sequence:
            return f"{'-' * len(subject_sequence)}\n{subject_sequence}"
        if not subject_sequence:
            return f"{query_sequence}\n{'-' * len(query_sequence)}"

        _, pointer_matrix = self(query_sequence, subject_sequence)

        qs, ss = [x.upper() for x in query_sequence], [
            x.upper() for x in subject_sequence
        ]
        i, j = len(qs), len(ss)
        query_align, subject_align = [], []
        # looks for match/mismatch/gap starting from bottom right of matrix
        while i > 0 or j > 0:
            if pointer_matrix[i, j] in [2, 5, 6, 10, 9, 13, 14, 17]:
                # appends match/mismatch then moves to the cell diagonally up and to the left
                query_align.append(qs[i - 1])
                subject_align.append(ss[j - 1])
                i -= 1
                j -= 1
            elif pointer_matrix[i, j] in [8, 10, 11, 12, 13, 14, 15, 17]:
                query_align.extend([qs[i - 1], qs[i - 2]])
                subject_align.extend([ss[j - 1], ss[j - 2]])
                i -= 2
                j -= 2
            elif pointer_matrix[i, j] in [3, 5, 7, 11, 9, 13, 15, 17]:
                # appends gap and accompanying nucleotide, then moves to the cell above
                subject_align.append("-")
                query_align.append(qs[i - 1])
                i -= 1
            elif pointer_matrix[i, j] in [4, 6, 7, 12, 9, 14, 15, 17]:
                # appends gap and accompanying nucleotide, then moves to the cell to the left
                subject_align.append(ss[j - 1])
                query_align.append("-")
                j -= 1

        query_align = "".join(query_align[::-1])
        subject_align = "".join(subject_align[::-1])
        return f"{query_align}\n{subject_align}"


class Hamming:
    def _check_inputs(
        self, query_sequence: str | int, subject_sequence: str | int
    ) -> None:
        if not isinstance(query_sequence, (str, int)) or not isinstance(
            subject_sequence, (str, int)
        ):
            raise TypeError("Sequences must be strings or integers")
        if type(query_sequence) is not type(subject_sequence):
            raise TypeError(
                "Sequences must be of the same type (both strings or both integers)"
            )
        if len(str(query_sequence)) != len(str(subject_sequence)) and not isinstance(
            query_sequence, int
        ):
            raise ValueError("Sequences must be of equal length")

    def __call__(
        self, query_sequence: str | int, subject_sequence: str | int
    ) -> tuple[int, list[int]]:
        self._check_inputs(query_sequence, subject_sequence)
        if isinstance(query_sequence, int) and isinstance(subject_sequence, int):
            qs, ss = bin(query_sequence)[2:], bin(subject_sequence)[2:]
            # Pad with leading zeros to make equal length
            max_len = max(len(qs), len(ss))
            qs = qs.zfill(max_len)
            ss = ss.zfill(max_len)
        else:
            qs = [x.upper() for x in query_sequence]
            ss = [x.upper() for x in subject_sequence]

        if len(qs) == 1 and len(ss) == 1:
            dist = 1 if qs != ss else 0
            dist_array = [dist]
            return dist, dist_array

        dist = 0
        dist_array = []
        for i, char in enumerate(qs):
            if char != ss[i]:
                dist += 1
                dist_array.append(1)
                continue
            dist_array.append(0)

        dist += len(ss) - len(qs)
        dist_array.extend([1] * (len(ss) - len(qs)))
        return dist, dist_array

    def distance(self, query_sequence: str | int, subject_sequence: str | int) -> int:
        self._check_inputs(query_sequence, subject_sequence)
        if isinstance(query_sequence, int) and isinstance(subject_sequence, int):
            qs, ss = int(query_sequence), int(subject_sequence)
            return bin(qs ^ ss).count("1")
        if len(query_sequence) == len(subject_sequence) == 0:
            return 0
        qs = [x.upper() for x in query_sequence]
        ss = [x.upper() for x in subject_sequence]
        query = set([(x, y) for (x, y) in enumerate(qs)])
        subject = set([(x, y) for (x, y) in enumerate(ss)])
        qs, sq = query - subject, subject - query
        dist = max(map(len, [qs, sq]))
        return dist

    def similarity(self, query_sequence: str | int, subject_sequence: str | int) -> int:
        self._check_inputs(query_sequence, subject_sequence)
        if isinstance(query_sequence, int) and isinstance(subject_sequence, int):
            qs, ss = int(query_sequence), int(subject_sequence)
            return bin(qs & ss).count("1")
        if len(query_sequence) == len(subject_sequence) == 0:
            return 1
        qs = [x.upper() for x in query_sequence]
        ss = [x.upper() for x in subject_sequence]
        query = set([(x, y) for (x, y) in enumerate(qs)])
        subject = set([(x, y) for (x, y) in enumerate(ss)])
        qs, sq = query - subject, subject - query
        sim = max(map(len, [query_sequence, subject_sequence])) - max(
            map(len, [qs, sq])
        )
        return sim

    def normalized_distance(self, query_sequence, subject_sequence) -> float:
        return self.distance(query_sequence, subject_sequence) / len(query_sequence)

    def normalized_similarity(self, query_sequence, subject_sequence) -> float:
        return 1 - self.normalized_distance(query_sequence, subject_sequence)

    def binary_distance_array(
        self, query_sequence: str, subject_sequence: str
    ) -> list[int]:
        self._check_inputs(query_sequence, subject_sequence)
        _, distarray = self(query_sequence, subject_sequence)
        return distarray

    def binary_similarity_array(
        self, query_sequence: str, subject_sequence: str
    ) -> list[int]:
        self._check_inputs(query_sequence, subject_sequence)
        _, distarray = self(query_sequence, subject_sequence)
        simarray = [1 if num == 0 else 0 for num in distarray]
        return simarray

    def matrix(self, qs: str, ss: str) -> None:
        return None

    def align(self, query_sequence: str | int, subject_sequence: str | int) -> str:
        self._check_inputs(query_sequence, subject_sequence)
        if isinstance(query_sequence, int) and isinstance(subject_sequence, int):
            qs, ss = int(query_sequence), int(subject_sequence)
            return f"{bin(qs)}\n{bin(ss)}"
        return f"{query_sequence}\n{subject_sequence}"


class NeedlemanWunsch(_GlobalBase):
    def __init__(
        self, match_score: int = 2, mismatch_penalty: int = 1, gap_penalty: int = 2
    ) -> None:
        self.match_score = match_score
        self.mismatch_penalty = mismatch_penalty
        self.gap_penalty = gap_penalty

    def __call__(
        self, query_sequence: str, subject_sequence: str
    ) -> tuple[NDArray[float64], NDArray[float64]]:
        qs, ss = [""], [""]
        qs.extend([x.upper() for x in query_sequence])
        ss.extend([x.upper() for x in subject_sequence])
        qs_len = len(qs)
        ss_len = len(ss)

        # matrix initialisation
        self.alignment_score = numpy.zeros((qs_len, ss_len))
        # pointer matrix to trace optimal alignment
        self.pointer = numpy.zeros((qs_len, ss_len))
        self.pointer[:, 0] = 3
        self.pointer[0, :] = 4
        # initialisation of starter values for first column and first row
        self.alignment_score[:, 0] = [-n * self.gap_penalty for n in range(qs_len)]
        self.alignment_score[0, :] = [-n * self.gap_penalty for n in range(ss_len)]

        for i in range(1, qs_len):
            for j in range(1, ss_len):
                if qs[i] == ss[j]:
                    match = self.alignment_score[i - 1][j - 1] + self.match_score
                else:
                    match = self.alignment_score[i - 1][j - 1] - self.mismatch_penalty
                ugap = self.alignment_score[i - 1][j] - self.gap_penalty
                lgap = self.alignment_score[i][j - 1] - self.gap_penalty
                tmax = max(match, lgap, ugap)

                self.alignment_score[i][j] = tmax  # highest value is best choice
                # matrix for traceback based on results from scoring matrix
                if match == tmax:
                    self.pointer[i, j] += 2
                if ugap == tmax:
                    self.pointer[i, j] += 3
                if lgap == tmax:
                    self.pointer[i, j] += 4
        return self.alignment_score, self.pointer

    def distance(self, query_sequence: str, subject_sequence: str) -> float:
        return super().distance(query_sequence, subject_sequence)

    def similarity(self, query_sequence: str, subject_sequence: str) -> float:
        return super().similarity(query_sequence, subject_sequence)

    def normalized_distance(self, query_sequence: str, subject_sequence: str) -> float:
        return super().normalized_distance(query_sequence, subject_sequence)

    def normalized_similarity(
        self, query_sequence: str, subject_sequence: str
    ) -> float:
        return super().normalized_similarity(query_sequence, subject_sequence)

    def matrix(self, query_sequence: str, subject_sequence: str) -> list[list[float]]:
        return super().matrix(query_sequence, subject_sequence)

    def align(self, query_sequence: str, subject_sequence: str) -> str:
        return super().align(query_sequence, subject_sequence)


class WatermanSmithBeyer(_GlobalBase):
    def __init__(
        self,
        match_score: int = 2,
        mismatch_penalty: int = 1,
        new_gap_penalty: int = 4,
        continue_gap_penalty: int = 1,
    ) -> None:
        self.match_score = match_score
        self.mismatch_penalty = mismatch_penalty
        self.new_gap_penalty = new_gap_penalty
        self.continue_gap_penalty = continue_gap_penalty

    def __call__(
        self, query_sequence: str, subject_sequence: str
    ) -> tuple[NDArray[float64], NDArray[float64]]:
        qs, ss = [""], [""]
        qs.extend([x.upper() for x in query_sequence])
        ss.extend([x.upper() for x in subject_sequence])
        qs_len = len(qs)
        ss_len = len(ss)

        # matrix initialisation
        self.alignment_score = numpy.zeros((qs_len, ss_len))
        # pointer matrix to trace optimal alignment
        self.pointer = numpy.zeros((qs_len, ss_len))
        self.pointer[:, 0] = 3
        self.pointer[0, :] = 4
        # initialisation of starter values for first column and first row
        self.alignment_score[:, 0] = [
            -self.new_gap_penalty + -n * self.continue_gap_penalty
            for n in range(qs_len)
        ]
        self.alignment_score[0, :] = [
            -self.new_gap_penalty + -n * self.continue_gap_penalty
            for n in range(ss_len)
        ]
        self.alignment_score[0][0] = 0

        for i in range(1, qs_len):
            for j in range(1, ss_len):
                if qs[i] == ss[j]:
                    match_score = self.alignment_score[i - 1][j - 1] + self.match_score
                else:
                    match_score = (
                        self.alignment_score[i - 1][j - 1] - self.mismatch_penalty
                    )
                # both gaps defaulted to continue gap penalty
                ugap_score = self.alignment_score[i - 1][j] - self.continue_gap_penalty
                lgap_score = self.alignment_score[i][j - 1] - self.continue_gap_penalty
                # if cell before i-1 or j-1 is gap, then this is a gap continuation
                if (
                    self.alignment_score[i - 1][j]
                    != (self.alignment_score[i - 2][j])
                    - self.new_gap_penalty
                    - self.continue_gap_penalty
                ):
                    ugap_score -= self.new_gap_penalty
                if (
                    self.alignment_score[i][j - 1]
                    != (self.alignment_score[i][j - 2])
                    - self.new_gap_penalty
                    - self.continue_gap_penalty
                ):
                    lgap_score -= self.new_gap_penalty
                tmax = max(match_score, lgap_score, ugap_score)

                self.alignment_score[i][j] = tmax  # highest value is best choice
                # matrix for traceback based on results from scoring matrix
                if match_score == tmax:
                    self.pointer[i, j] += 2
                elif ugap_score == tmax:
                    self.pointer[i, j] += 3
                elif lgap_score == tmax:
                    self.pointer[i, j] += 4
        return self.alignment_score, self.pointer

    def distance(self, query_sequence: str, subject_sequence: str) -> float:
        return super().distance(query_sequence, subject_sequence)

    def similarity(self, query_sequence: str, subject_sequence: str) -> float:
        return super().similarity(query_sequence, subject_sequence)

    def normalized_distance(self, query_sequence: str, subject_sequence: str) -> float:
        return super().normalized_distance(query_sequence, subject_sequence)

    def normalized_similarity(
        self, query_sequence: str, subject_sequence: str
    ) -> float:
        return super().normalized_similarity(query_sequence, subject_sequence)

    def matrix(self, query_sequence: str, subject_sequence: str) -> list[list[float]]:
        return super().matrix(query_sequence, subject_sequence)

    def align(self, query_sequence: str, subject_sequence: str) -> str:
        return super().align(query_sequence, subject_sequence)


class Gotoh(_GlobalBase):
    def __init__(
        self,
        match_score: int = 2,
        mismatch_penalty: int = 1,
        new_gap_penalty: int = 2,
        continue_gap_penalty: int = 1,
    ) -> None:
        self.match_score = match_score
        self.mismatch_penalty = mismatch_penalty
        self.new_gap_penalty = new_gap_penalty
        self.continue_gap_penalty = continue_gap_penalty

    def __call__(
        self, query_sequence: str, subject_sequence: str
    ) -> tuple[NDArray[float64], NDArray[float64], NDArray[float64], NDArray[float64]]:
        qs, ss = [""], [""]
        qs.extend([x.upper() for x in query_sequence])
        ss.extend([x.upper() for x in subject_sequence])

        # matrix initialisation
        self.D = numpy.full((len(qs), len(ss)), -numpy.inf)
        self.P = numpy.full((len(qs), len(ss)), -numpy.inf)
        self.P[:, 0] = 0
        self.Q = numpy.full((len(qs), len(ss)), -numpy.inf)
        self.Q[0, :] = 0
        self.pointer = numpy.zeros((len(qs), len(ss)))
        self.pointer[:, 0] = 3
        self.pointer[0, :] = 4
        # initialisation of starter values for first column and first row
        self.D[0, 0] = 0
        # Initialize first column (vertical gaps)
        for i in range(1, len(qs)):
            self.D[i, 0] = -(self.new_gap_penalty + (i) * self.continue_gap_penalty)
        # Initialize first row (horizontal gaps)
        for j in range(1, len(ss)):
            self.D[0, j] = -(self.new_gap_penalty + (j) * self.continue_gap_penalty)

        for i in range(1, len(qs)):
            for j in range(1, len(ss)):
                match = self.D[i - 1, j - 1] + (
                    self.match_score if qs[i] == ss[j] else -self.mismatch_penalty
                )
                self.P[i, j] = max(
                    self.D[i - 1, j] - self.new_gap_penalty - self.continue_gap_penalty,
                    self.P[i - 1, j] - self.continue_gap_penalty,
                )
                self.Q[i, j] = max(
                    self.D[i, j - 1] - self.new_gap_penalty - self.continue_gap_penalty,
                    self.Q[i, j - 1] - self.continue_gap_penalty,
                )
                self.D[i, j] = max(match, self.P[i, j], self.Q[i, j])
                # matrix for traceback based on results from scoring matrix
                if self.D[i, j] == match:
                    self.pointer[i, j] += 2
                if self.D[i, j] == self.P[i, j]:
                    self.pointer[i, j] += 3
                if self.D[i, j] == self.Q[i, j]:
                    self.pointer[i, j] += 4

        return self.D, self.P, self.Q, self.pointer

    def distance(self, query_sequence: str, subject_sequence: str) -> float:
        return super().distance(query_sequence, subject_sequence)

    def similarity(self, query_sequence: str, subject_sequence: str) -> float:
        if query_sequence == subject_sequence == "":
            return self.match_score
        D, _, _, _ = self(query_sequence, subject_sequence)
        return float(D[D.shape[0] - 1, D.shape[1] - 1])

    def normalized_distance(self, query_sequence: str, subject_sequence: str) -> float:
        return super().normalized_distance(query_sequence, subject_sequence)

    def normalized_similarity(
        self, query_sequence: str, subject_sequence: str
    ) -> float:
        return super().normalized_similarity(query_sequence, subject_sequence)

    def matrix(
        self, query_sequence: str, subject_sequence: str
    ) -> tuple[NDArray[float64], NDArray[float64], NDArray[float64]]:
        D, P, Q, _ = self(query_sequence, subject_sequence)
        return D, P, Q

    def align(self, query_sequence: str, subject_sequence: str) -> str:
        _, _, _, pointer_matrix = self(query_sequence, subject_sequence)

        qs, ss = [x.upper() for x in query_sequence], [
            x.upper() for x in subject_sequence
        ]
        i, j = len(qs), len(ss)
        query_align, subject_align = [], []

        # looks for match/mismatch/gap starting from bottom right of matrix
        while i > 0 or j > 0:
            if pointer_matrix[i, j] in [3, 5, 7, 9]:
                # appends gap and accompanying nucleotide, then moves to the cell above
                subject_align.append("-")
                query_align.append(qs[i - 1])
                i -= 1
            elif pointer_matrix[i, j] in [4, 6, 7, 9]:
                # appends gap and accompanying nucleotide, then moves to the cell to the left
                subject_align.append(ss[j - 1])
                query_align.append("-")
                j -= 1
            elif pointer_matrix[i, j] in [2, 5, 6, 9]:
                # appends match/mismatch then moves to the cell diagonally up and to the left
                query_align.append(qs[i - 1])
                subject_align.append(ss[j - 1])
                i -= 1
                j -= 1

        query_align = "".join(query_align[::-1])
        subject_align = "".join(subject_align[::-1])

        return f"{query_align}\n{subject_align}"


class GotohLocal(_LocalBase):
    def __init__(
        self,
        match_score=2,
        mismatch_penalty=1,
        new_gap_penalty=3,
        continue_gap_penalty=2,
    ):
        self.match_score = match_score
        self.mismatch_penalty = mismatch_penalty
        self.new_gap_penalty = new_gap_penalty
        self.continue_gap_penalty = continue_gap_penalty

    def __call__(
        self, query_sequence: str, subject_sequence: str
    ) -> tuple[NDArray, NDArray, NDArray]:
        """Compute single alignment matrix"""
        # Initialize matrices
        D = numpy.zeros((len(query_sequence) + 1, len(subject_sequence) + 1))
        P = numpy.zeros((len(query_sequence) + 1, len(subject_sequence) + 1))
        Q = numpy.zeros((len(query_sequence) + 1, len(subject_sequence) + 1))

        # Fill matrices
        for i in range(1, len(query_sequence) + 1):
            for j in range(1, len(subject_sequence) + 1):
                score = (
                    self.match_score
                    if query_sequence[i - 1].upper() == subject_sequence[j - 1].upper()
                    else -self.mismatch_penalty
                )
                P[i, j] = max(
                    D[i - 1, j] - self.new_gap_penalty,
                    P[i - 1, j] - self.continue_gap_penalty,
                )
                Q[i, j] = max(
                    D[i, j - 1] - self.new_gap_penalty,
                    Q[i, j - 1] - self.continue_gap_penalty,
                )
                D[i, j] = max(0, D[i - 1, j - 1] + score, P[i, j], Q[i, j])

        return D, P, Q

    def distance(self, query_sequence: str, subject_sequence: str) -> float:
        query_length = len(query_sequence)
        subject_length = len(subject_sequence)
        if not query_sequence and not subject_sequence:
            return 0.0
        if not query_sequence or not subject_sequence:
            return max(query_length, subject_length)

        matrix, _, _ = self(query_sequence, subject_sequence)
        sim_AB = matrix.max()
        max_score = self.match_score * max(query_length, subject_length)
        return max_score - sim_AB

    def similarity(self, query_sequence: str, subject_sequence: str) -> float:
        if not query_sequence and not subject_sequence:
            return 1.0
        matrix, _, _ = self(query_sequence, subject_sequence)
        return matrix.max()

    def normalized_distance(self, query_sequence: str, subject_sequence: str) -> float:
        return super().normalized_distance(query_sequence, subject_sequence)

    def normalized_similarity(
        self, query_sequence: str, subject_sequence: str
    ) -> float:
        """Calculate normalized similarity between 0 and 1"""
        if not query_sequence and not subject_sequence:
            return 1.0
        if not query_sequence or not subject_sequence:
            return 0.0
        matrix, _, _ = self(query_sequence, subject_sequence)
        score = matrix.max()
        return score / (
            min(len(query_sequence), len(subject_sequence)) * self.match_score
        )

    def matrix(
        self, query_sequence: str, subject_sequence: str
    ) -> tuple[NDArray[float64], NDArray[float64], NDArray[float64]]:
        D, P, Q = self(query_sequence, subject_sequence)
        return D, P, Q

    def align(self, query_sequence: str, subject_sequence: str) -> str:
        matrix, _, _ = self(query_sequence, subject_sequence)

        qs = [x.upper() for x in query_sequence]
        ss = [x.upper() for x in subject_sequence]
        if matrix.max() == 0:
            return ""

        # finds the largest value closest to bottom right of matrix
        i, j = numpy.unravel_index(matrix.argmax(), matrix.shape)

        subject_align = []
        query_align = []
        score = matrix.max()
        while score > 0:
            score = matrix[i][j]
            if score == 0:
                break
            query_align.append(qs[i - 1])
            subject_align.append(ss[j - 1])
            i -= 1
            j -= 1
        query_align = "".join(query_align[::-1])
        subject_align = "".join(subject_align[::-1])
        return f"{query_align}\n{subject_align}"


class Hirschberg:
    def __init__(
        self, match_score: int = 1, mismatch_penalty: int = 2, gap_penalty: int = 4
    ) -> None:
        self.match_score = match_score
        self.mismatch_penalty = mismatch_penalty
        self.gap_penalty = gap_penalty

    def __call__(self, query_sequence: str, subject_sequence: str) -> str:
        qs = "".join([x.upper() for x in query_sequence])
        ss = "".join([x.upper() for x in subject_sequence])

        if len(qs) == 0:
            return f"{'-' * len(ss)}\n{ss}"
        elif len(ss) == 0:
            return f"{qs}\n{'-' * len(qs)}"
        elif len(qs) == 1 or len(ss) == 1:
            return self._align_simple(qs, ss)

        # Divide and conquer
        xmid = len(qs) // 2

        # Forward score from start to mid
        score_left = self._score(qs[:xmid], ss)
        # Backward score from end to mid
        score_right = self._score(qs[xmid:][::-1], ss[::-1])[::-1]

        # Find optimal split point in subject sequence
        total_scores = score_left + score_right
        ymid = numpy.argmin(total_scores)

        # Recursively align both halves
        left_align = self(qs[:xmid], ss[:ymid])
        right_align = self(qs[xmid:], ss[ymid:])

        # Combine the alignments
        left_q, left_s = left_align.split("\n")
        right_q, right_s = right_align.split("\n")
        return f"{left_q + right_q}\n{left_s + right_s}"

    def _score(self, qs: str, ss: str) -> NDArray[float64]:
        # Calculate forward/backward score profile
        prev_row = numpy.zeros(len(ss) + 1, dtype=float64)
        curr_row = numpy.zeros(len(ss) + 1, dtype=float64)

        # Initialize first row
        for j in range(1, len(ss) + 1):
            prev_row[j] = prev_row[j - 1] + self.gap_penalty

        # Fill matrix
        for i in range(1, len(qs) + 1):
            curr_row[0] = prev_row[0] + self.gap_penalty
            for j in range(1, len(ss) + 1):
                match_score = (
                    -self.match_score
                    if qs[i - 1] == ss[j - 1]
                    else self.mismatch_penalty
                )
                curr_row[j] = min(
                    prev_row[j - 1] + match_score,  # match/mismatch
                    prev_row[j] + self.gap_penalty,  # deletion
                    curr_row[j - 1] + self.gap_penalty,  # insertion
                )
            prev_row, curr_row = curr_row, prev_row

        return prev_row

    def _align_simple(self, qs: str, ss: str) -> str:
        score = numpy.zeros((len(qs) + 1, len(ss) + 1), dtype=float64)
        pointer = numpy.zeros((len(qs) + 1, len(ss) + 1), dtype=float64)

        # Initialize first row and column
        for i in range(1, len(qs) + 1):
            score[i, 0] = score[i - 1, 0] + self.gap_penalty
            pointer[i, 0] = 1
        for j in range(1, len(ss) + 1):
            score[0, j] = score[0, j - 1] + self.gap_penalty
            pointer[0, j] = 2

        # Fill matrices
        for i in range(1, len(qs) + 1):
            for j in range(1, len(ss) + 1):
                match_score = (
                    -self.match_score
                    if qs[i - 1] == ss[j - 1]
                    else self.mismatch_penalty
                )
                diag = score[i - 1, j - 1] + match_score
                up = score[i - 1, j] + self.gap_penalty
                left = score[i, j - 1] + self.gap_penalty

                score[i, j] = min(diag, up, left)
                if score[i, j] == diag:
                    pointer[i, j] = 3
                elif score[i, j] == up:
                    pointer[i, j] = 1
                else:
                    pointer[i, j] = 2

        # Traceback
        i, j = len(qs), len(ss)
        query_align, subject_align = [], []

        while i > 0 or j > 0:
            if i > 0 and j > 0 and pointer[i, j] == 3:
                query_align.append(qs[i - 1])
                subject_align.append(ss[j - 1])
                i -= 1
                j -= 1
            elif i > 0 and pointer[i, j] == 1:
                query_align.append(qs[i - 1])
                subject_align.append("-")
                i -= 1
            else:
                query_align.append("-")
                subject_align.append(ss[j - 1])
                j -= 1

        return f"{''.join(query_align[::-1])}\n{''.join(subject_align[::-1])}"

    def distance(self, query_sequence: str, subject_sequence: str) -> float:
        """Calculate edit distance between sequences"""
        if not query_sequence and not subject_sequence:
            return 0.0
        if not query_sequence:
            return self.gap_penalty * len(subject_sequence)
        if not subject_sequence:
            return self.gap_penalty * len(query_sequence)

        alignment = self(query_sequence, subject_sequence)
        query_align, subject_align = alignment.split("\n")

        dist = 0.0
        for q, s in zip(query_align, subject_align):
            if q == "-" or s == "-":
                dist += self.gap_penalty
            elif q != s:
                dist += self.mismatch_penalty
            # No reduction for matches in distance calculation
        return float(dist)

    def similarity(self, query_sequence: str, subject_sequence: str) -> float:
        """Calculate similarity score between sequences"""
        if not query_sequence and not subject_sequence:
            return 1.0
        if not query_sequence or not subject_sequence:
            return 0.0
        alignment = self(query_sequence, subject_sequence)
        query_align, subject_align = alignment.split("\n")

        score = 0.0
        for q, s in zip(query_align, subject_align):
            if q == s and q != "-":
                score += self.match_score
            elif q == "-" or s == "-":
                score -= self.gap_penalty
            else:
                score -= self.mismatch_penalty
        return max(0.0, float(score))

    def normalized_distance(self, query_sequence: str, subject_sequence: str) -> float:
        """Calculate normalized distance between sequences"""
        if not query_sequence or not subject_sequence:
            return 1.0
        if query_sequence == subject_sequence:
            return 0.0

        raw_dist = self.distance(query_sequence, subject_sequence)
        max_len = max(len(query_sequence), len(subject_sequence))
        worst_score = max_len * self.mismatch_penalty

        if worst_score == 0:
            return 0.0
        return min(1.0, raw_dist / worst_score)

    def normalized_similarity(
        self, query_sequence: str, subject_sequence: str
    ) -> float:
        """Calculate normalized similarity between sequences"""
        if not query_sequence or not subject_sequence:
            return 0.0
        if query_sequence == subject_sequence:
            return 1.0

        return 1.0 - self.normalized_distance(query_sequence, subject_sequence)

    def matrix(self, query_sequence: str, subject_sequence: str) -> NDArray[float64]:
        if len(query_sequence) <= 1 or len(subject_sequence) <= 1:
            score = numpy.zeros(
                (len(query_sequence) + 1, len(subject_sequence) + 1), dtype=float64
            )
            for i in range(len(query_sequence) + 1):
                score[i, 0] = i * self.gap_penalty
            for j in range(len(subject_sequence) + 1):
                score[0, j] = j * self.gap_penalty
            for i in range(1, len(query_sequence) + 1):
                for j in range(1, len(subject_sequence) + 1):
                    match_score = (
                        -self.match_score
                        if query_sequence[i - 1] == subject_sequence[j - 1]
                        else self.mismatch_penalty
                    )
                    score[i, j] = min(
                        score[i - 1, j - 1] + match_score,
                        score[i - 1, j] + self.gap_penalty,
                        score[i, j - 1] + self.gap_penalty,
                    )
            return score
        return numpy.array([[]], dtype=float64)

    def align(self, query_sequence: str, subject_sequence: str) -> str:
        return self(query_sequence, subject_sequence)


class Jaro:
    def __init__(self) -> None:
        self.match_score = 1
        self.winkler = False
        self.scaling_factor = 1

    def __call__(self, query_sequence: str, subject_sequence: str) -> tuple[int, int]:
        qs, ss = (x.upper() for x in [query_sequence, subject_sequence])
        if qs == ss:
            return -1, 0
        qs_len, ss_len = len(query_sequence), len(subject_sequence)
        max_dist = max(qs_len, ss_len) // 2 - 1

        matches = 0
        array_qs = [False] * qs_len
        array_ss = [False] * ss_len
        for i in range(qs_len):
            start = max(0, i - max_dist)
            end = min(ss_len, i + max_dist + 1)
            for j in range(start, end):
                if qs[i] == ss[j] and array_ss[j] == 0:
                    array_qs[i] = array_ss[j] = True
                    matches += 1
                    break
        if matches == 0:
            return 0, 0

        transpositions = 0
        comparison = 0
        for i in range(qs_len):
            if array_qs[i]:
                while not array_ss[comparison]:
                    comparison += 1
                if qs[i] != ss[comparison]:
                    transpositions += 1
                comparison += 1
        return matches, transpositions // 2

    def distance(self, query_sequence: str, subject_sequence: str) -> float:
        return 1 - self.similarity(query_sequence, subject_sequence)

    def similarity(self, query_sequence: str, subject_sequence: str) -> float:
        if not query_sequence or not subject_sequence:
            return 1.0 if query_sequence == subject_sequence else 0.0

        matches, t = self(query_sequence, subject_sequence)
        if matches == 0:
            return 0.0
        if matches == -1:
            return 1.0

        len_qs, len_ss = len(query_sequence), len(subject_sequence)
        jaro_sim = (1 / 3) * (
            (matches / len_qs) + (matches / len_ss) + ((matches - t) / matches)
        )

        if not self.winkler:
            return jaro_sim

        prefix_matches = 0
        max_prefix = min(4, min(len_qs, len_ss))
        for i in range(max_prefix):
            if (
                query_sequence[i] != subject_sequence[i]
                or i > len(subject_sequence) - 1
            ):
                break
            prefix_matches += 1
        return jaro_sim + prefix_matches * self.scaling_factor * (1 - jaro_sim)

    def normalized_distance(self, query_sequence: str, subject_sequence: str) -> float:
        return self.distance(query_sequence, subject_sequence)

    def normalized_similarity(
        self, query_sequence: str, subject_sequence: str
    ) -> float:
        return self.similarity(query_sequence, subject_sequence)

    def matrix(self, query_sequence: str, subject_sequence: str) -> NDArray[float64]:
        # dynamic programming variant to show all matches
        qs, ss = [""], [""]
        qs.extend([x.upper() for x in query_sequence])
        ss.extend([x.upper() for x in subject_sequence])
        max_match_dist = max(0, (max(len(ss) - 1, len(qs) - 1) // 2) - 1)

        # matrix initialization
        self.alignment_score = numpy.zeros((len(qs), len(ss)))
        for i, query_char in enumerate(qs):
            for j, subject_char in enumerate(ss):
                if i == 0 or j == 0:
                    # keeps first row and column consistent throughout all calculations
                    continue
                dmatch = self.alignment_score[i - 1][j - 1]
                start = max(1, i - max_match_dist)
                trans_match = ss[start : start + (2 * max_match_dist)]
                if query_char == subject_char or query_char in trans_match:
                    dmatch += 1

                self.alignment_score[i][j] = dmatch
        return self.alignment_score

    def align(self, query_sequence: str, subject_sequence: str) -> str:
        """Return aligned sequences showing matches."""
        qs = [x.upper() for x in query_sequence]
        ss = [x.upper() for x in subject_sequence]
        if qs == ss:
            return f"{''.join(qs)}\n{''.join(ss)}"

        # Initialize arrays for tracking matches
        array_qs = [False] * len(qs)
        array_ss = [False] * len(ss)
        max_dist = max(len(qs), len(ss)) // 2 - 1

        # First pass: mark matches
        for i in range(len(qs)):
            start = max(0, i - max_dist)
            end = min(len(ss), i + max_dist + 1)
            for j in range(start, end):
                if qs[i] == ss[j] and not array_ss[j]:
                    array_qs[i] = array_ss[j] = True
                    break

        # Build global alignment
        query_align, subject_align = [], []
        i = j = 0

        while i < len(qs) or j < len(ss):
            if (
                i < len(qs)
                and j < len(ss)
                and array_qs[i]
                and array_ss[j]
                and qs[i] == ss[j]
            ):
                # Add match
                query_align.append(qs[i])
                subject_align.append(ss[j])
                i += 1
                j += 1
            elif i < len(qs) and not array_qs[i]:
                # Add unmatched query character
                query_align.append(qs[i])
                subject_align.append("-")
                i += 1
            elif j < len(ss) and not array_ss[j]:
                # Add unmatched subject character
                query_align.append("-")
                subject_align.append(ss[j])
                j += 1
            elif i < len(qs) and j < len(ss):
                query_align.append(qs[i])
                subject_align.append(ss[j])
                i += 1
                j += 1
            elif i < len(qs):  # Remaining query characters
                query_align.append(qs[i])
                subject_align.append("-")
                i += 1
            elif j < len(ss):  # Remaining subject characters
                query_align.append("-")
                subject_align.append(ss[j])
                j += 1

        return f"{''.join(query_align)}\n{''.join(subject_align)}"


class JaroWinkler(Jaro):
    def __init__(self, scaling_factor=0.1):
        self.match_score = 1
        self.winkler = True
        # scaling factor should not exceed 0.25 else similarity could be larger than 1
        self.scaling_factor = scaling_factor


class SmithWaterman:
    def __init__(
        self, match_score: int = 1, mismatch_penalty: int = 1, gap_penalty: int = 2
    ) -> None:
        self.match_score = match_score
        self.mismatch_penalty = mismatch_penalty
        self.gap_penalty = gap_penalty

    def __call__(self, query_sequence: str, subject_sequence: str) -> NDArray[float64]:
        qs, ss = [""], [""]
        qs.extend([x.upper() for x in query_sequence])
        ss.extend([x.upper() for x in subject_sequence])
        qs_len = len(qs)
        ss_len = len(ss)

        # matrix initialisation
        self.alignment_score = numpy.zeros((qs_len, ss_len))
        for i in range(1, qs_len):
            for j in range(1, ss_len):
                if qs[i] == ss[j]:
                    match = self.alignment_score[i - 1][j - 1] + self.match_score
                else:
                    match = self.alignment_score[i - 1][j - 1] - self.mismatch_penalty
                ugap = self.alignment_score[i - 1][j] - self.gap_penalty
                lgap = self.alignment_score[i][j - 1] - self.gap_penalty
                tmax = max(0, match, lgap, ugap)
                self.alignment_score[i][j] = tmax
        return self.alignment_score

    def distance(self, query_sequence: str, subject_sequence: str) -> float:
        if not query_sequence and not subject_sequence:
            return 0
        return max(map(len, [query_sequence, subject_sequence])) - self.similarity(
            query_sequence, subject_sequence
        )

    def similarity(self, query_sequence: str, subject_sequence: str) -> float:
        if not query_sequence and not subject_sequence:
            return 1.0
        matrix = self(query_sequence, subject_sequence)
        return matrix.max()

    def normalized_distance(self, query_sequence: str, subject_sequence: str) -> float:
        if not query_sequence and not subject_sequence:
            return 0
        dist = self.distance(query_sequence, subject_sequence)
        return dist / max(map(len, [query_sequence, subject_sequence]))

    def normalized_similarity(
        self, query_sequence: str, subject_sequence: str
    ) -> float:
        if not query_sequence and not subject_sequence:
            return 1
        similarity = self.similarity(query_sequence, subject_sequence)
        return similarity / max(map(len, [query_sequence, subject_sequence]))

    def matrix(self, query_sequence: str, subject_sequence: str) -> NDArray[float64]:
        matrix = self(query_sequence, subject_sequence)
        return matrix

    def align(self, query_sequence: str, subject_sequence: str) -> str:
        matrix = self(query_sequence, subject_sequence)

        qs = [x.upper() for x in query_sequence]
        ss = [x.upper() for x in subject_sequence]
        if matrix.max() == 0:
            return "There is no local alignment!"

        # finds the largest value closest to bottom right of matrix
        i, j = list(numpy.where(matrix == matrix.max()))
        i, j = i[-1], j[-1]

        subject_align = []
        query_align = []
        score = matrix.max()
        while score > 0:
            score = matrix[i][j]
            if score == 0:
                break
            query_align.append(qs[i - 1])
            subject_align.append(ss[j - 1])
            i -= 1
            j -= 1
        query_align = "".join(query_align[::-1])
        subject_align = "".join(subject_align[::-1])
        return f"{query_align}\n{subject_align}"


class LongestCommonSubsequence(_LocalBase):
    def __init__(self):
        self.match_score = 1

    def __call__(self, query_sequence: str, subject_sequence: str) -> NDArray[float64]:
        qs, ss = [""], [""]
        qs.extend([x.upper() for x in query_sequence])
        ss.extend([x.upper() for x in subject_sequence])
        qs_len = len(qs)
        ss_len = len(ss)

        # matrix initialisation
        self.alignment_score = numpy.zeros((qs_len, ss_len))
        for i in range(1, qs_len):
            for j in range(1, ss_len):
                if qs[i] == ss[j]:
                    match = self.alignment_score[i - 1][j - 1] + self.match_score
                else:
                    match = max(
                        self.alignment_score[i][j - 1], self.alignment_score[i - 1][j]
                    )
                self.alignment_score[i][j] = match

        return self.alignment_score

    def distance(self, query_sequence: str, subject_sequence: str) -> float:
        return super().distance(query_sequence, subject_sequence)

    def similarity(self, query_sequence: str, subject_sequence: str) -> float:
        return super().similarity(query_sequence, subject_sequence)

    def normalized_distance(self, query_sequence: str, subject_sequence: str) -> float:
        return super().normalized_distance(query_sequence, subject_sequence)

    def normalized_similarity(
        self, query_sequence: str, subject_sequence: str
    ) -> float:
        return super().normalized_similarity(query_sequence, subject_sequence)

    def matrix(self, query_sequence: str, subject_sequence: str) -> NDArray:
        return super().matrix(query_sequence, subject_sequence)

    def align(self, query_sequence: str, subject_sequence: str) -> str:
        matrix = self(query_sequence, subject_sequence)

        qs = [x.upper() for x in query_sequence]
        ss = [x.upper() for x in subject_sequence]

        longest_match = numpy.max(matrix)
        if longest_match <= 1:
            return []

        longest_subseqs = set()
        positions = numpy.argwhere(matrix == longest_match)
        for position in positions:
            temp = []
            i, j = position
            while i != 0 and j != 0:
                if qs[i - 1] == ss[j - 1]:
                    temp.append(qs[i - 1])
                    i -= 1
                    j -= 1
                elif matrix[i - 1, j] >= matrix[i, j - 1]:
                    i -= 1
                elif matrix[i, j - 1] >= matrix[i - 1, j]:
                    j -= 1
            longest_subseqs.add("".join(temp[::-1]))
        return list(longest_subseqs)


class LongestCommonSubstring(_LocalBase):
    def __init__(self):
        self.match_score = 1

    def __call__(self, query_sequence: str, subject_sequence: str):
        qs, ss = [""], [""]
        qs.extend([x.upper() for x in query_sequence])
        ss.extend([x.upper() for x in subject_sequence])
        qs_len = len(qs)
        ss_len = len(ss)

        # matrix initialisation
        alignment_matrix = numpy.zeros((qs_len, ss_len))
        for i in range(1, qs_len):
            for j in range(1, ss_len):
                if qs[i] == ss[j]:
                    match = alignment_matrix[i - 1][j - 1] + self.match_score
                else:
                    match = 0
                alignment_matrix[i][j] = match
        return alignment_matrix

    def distance(self, query_sequence: str, subject_sequence: str) -> float:
        return super().distance(query_sequence, subject_sequence)

    def similarity(self, query_sequence: str, subject_sequence: str) -> float:
        return super().similarity(query_sequence, subject_sequence)

    def normalized_distance(self, query_sequence: str, subject_sequence: str) -> float:
        return super().normalized_distance(query_sequence, subject_sequence)

    def normalized_similarity(
        self, query_sequence: str, subject_sequence: str
    ) -> float:
        return super().normalized_similarity(query_sequence, subject_sequence)

    def matrix(self, query_sequence: str, subject_sequence: str) -> NDArray:
        return super().matrix(query_sequence, subject_sequence)

    def align(self, query_sequence, subject_sequence):
        matrix = self(query_sequence, subject_sequence)

        longest_match = numpy.max(matrix)
        if longest_match <= 1:
            return [""]

        longest_substrings = set()
        positions = numpy.argwhere(matrix == longest_match)
        for position in positions:
            temp = []
            i, j = position
            while matrix[i][j] != 0:
                temp.append(query_sequence[i - 1])
                i -= 1
                j -= 1
            longest_substrings.add("".join(temp[::-1]))
        return list(longest_substrings)


class ShortestCommonSupersequence:
    def __call__(self, query_sequence: str, subject_sequence: str) -> NDArray[float64]:
        qs, ss = [""], [""]
        qs.extend([x.upper() for x in query_sequence])
        ss.extend([x.upper() for x in subject_sequence])
        qs_len = len(qs)
        ss_len = len(ss)

        # Matrix initialization with correct shape
        self.alignment_score = numpy.zeros((qs_len, ss_len), dtype=float64)

        # Fill first row and column
        self.alignment_score[:, 0] = [i for i in range(qs_len)]
        self.alignment_score[0, :] = [j for j in range(ss_len)]
        # Fill rest of matrix
        for i in range(1, qs_len):
            for j in range(1, ss_len):
                if qs[i] == ss[j]:
                    self.alignment_score[i, j] = self.alignment_score[i - 1, j - 1]
                else:
                    self.alignment_score[i, j] = min(
                        self.alignment_score[i - 1, j] + 1,
                        self.alignment_score[i, j - 1] + 1,
                    )
        return self.alignment_score

    def distance(self, query_sequence: str, subject_sequence: str) -> float:
        """Return length of SCS minus length of longer sequence"""
        if not query_sequence or not subject_sequence:
            return max(len(query_sequence), len(subject_sequence))

        matrix = self(query_sequence, subject_sequence)
        return matrix[matrix.shape[0] - 1, matrix.shape[1] - 1]

    def similarity(self, query_sequence: str, subject_sequence: str) -> float:
        """Calculate similarity based on matching positions in supersequence.

        Similarity is the number of positions where characters match between
        the query sequence and the shortest common supersequence.
        """
        if not query_sequence or not subject_sequence:
            return 0.0

        scs = self.align(query_sequence, subject_sequence)
        return len(scs) - self.distance(query_sequence, subject_sequence)

    def normalized_distance(self, query_sequence: str, subject_sequence: str) -> float:
        """Calculate normalized distance between sequences"""
        if not query_sequence or not subject_sequence:
            return 1.0 if (query_sequence or subject_sequence) else 0.0
        if query_sequence == subject_sequence == "":
            return 0.0
        alignment_len = len(self.align(query_sequence, subject_sequence))
        distance = self.distance(query_sequence, subject_sequence)
        return distance / alignment_len

    def normalized_similarity(
        self, query_sequence: str, subject_sequence: str
    ) -> float:
        """Calculate normalized similarity between sequences"""
        return 1.0 - self.normalized_distance(query_sequence, subject_sequence)

    def matrix(self, query_sequence: str, subject_sequence: str) -> NDArray[float64]:
        return self(query_sequence, subject_sequence)

    def align(self, query_sequence: str, subject_sequence: str) -> str:
        if not query_sequence:
            return subject_sequence
        if not subject_sequence:
            return query_sequence

        matrix = self(query_sequence, subject_sequence)
        qs = [x.upper() for x in query_sequence]
        ss = [x.upper() for x in subject_sequence]

        i, j = len(qs), len(ss)
        result = []

        while i > 0 and j > 0:
            if qs[i - 1] == ss[j - 1]:
                result.append(qs[i - 1])
                i -= 1
                j -= 1
            elif matrix[i, j - 1] <= matrix[i - 1, j]:
                result.append(ss[j - 1])
                j -= 1
            else:
                result.append(qs[i - 1])
                i -= 1

        # Add remaining characters
        while i > 0:
            result.append(qs[i - 1])
            i -= 1
        while j > 0:
            result.append(ss[j - 1])
            j -= 1

        return "".join(reversed(result))


hamming = Hamming()
wagner_fischer = WagnerFischer()
needleman_wunsch = NeedlemanWunsch()
waterman_smith_beyer = WatermanSmithBeyer()
smith_waterman = SmithWaterman()
hirschberg = Hirschberg()
jaro = Jaro()
jaro_winkler = JaroWinkler()
lowrance_wagner = LowranceWagner()
longest_common_subsequence = LongestCommonSubsequence()
longest_common_substring = LongestCommonSubstring()
shortest_common_supersequence = ShortestCommonSupersequence()
gotoh = Gotoh()
gotoh_local = GotohLocal()

if __name__ == "__main__":
    main()
