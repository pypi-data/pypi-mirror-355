from typing_extensions import Self

from pydantic import BaseModel

from vizitig.types import DNAPython, KmerPython


class Alignment(BaseModel):
    score: int | float
    align_seq1: list[str | None]
    align_seq2: list[str | None]

    @classmethod
    def from_seq(cls, s1: str, s2: str) -> Self:
        aligner = cls.alignment
        alignement1 = aligner(  # type: ignore
            s1,
            s2,
        )
        alignement2 = aligner(  # type: ignore
            str(
                KmerPython.from_sequence(
                    next(DNAPython.from_str(s1))
                ).reverse_complement()
            ),
            s2,
        )
        alignement = max(alignement1, alignement2, key=lambda e: e[2])

        return cls(
            score=alignement[2],
            align_seq1=[e for e in alignement[0]],
            align_seq2=[e for e in alignement[1]],
        )

    @classmethod
    def alignment(
        cls,
        seq1,
        seq2,
        match_score=10,
        mismatch_score=-100,
        gap_open=-100,
        gap_extend=0,
    ):
        n, m = len(seq1), len(seq2)

        # Use native Python lists instead of NumPy arrays
        score_matrix = [[0] * (m + 1) for _ in range(n + 1)]
        traceback = [[0] * (m + 1) for _ in range(n + 1)]

        for i in range(1, n + 1):
            score_matrix[i][0] = 0
            traceback[i][0] = 2

        for j in range(1, m + 1):
            score_matrix[0][j] = 0
            traceback[0][j] = 1

        for i in range(1, n + 1):
            for j in range(1, m + 1):
                match = score_matrix[i - 1][j - 1] + (
                    match_score if seq1[i - 1] == seq2[j - 1] else mismatch_score
                )
                delete = score_matrix[i - 1][j] + (
                    gap_extend if traceback[i - 1][j] == 2 else gap_open
                )
                insert = score_matrix[i][j - 1] + (
                    gap_extend if traceback[i][j - 1] == 1 else gap_open
                )

                score_matrix[i][j] = max(match, delete, insert)

                if score_matrix[i][j] == match:
                    traceback[i][j] = 0
                elif score_matrix[i][j] == insert:
                    traceback[i][j] = 1
                else:
                    traceback[i][j] = 2

        max_score = max(max(score_matrix[n]), max(row[m] for row in score_matrix))
        if max(score_matrix[n]) >= max(row[m] for row in score_matrix):
            i, j = n, score_matrix[n].index(max(score_matrix[n]))
        else:
            i, j = max((row[m], idx) for idx, row in enumerate(score_matrix))[1], m

        aligned_seq1, aligned_seq2 = "", ""

        while i > 0 or j > 0:
            if i == 0:
                aligned_seq1 = "-" + aligned_seq1
                aligned_seq2 = seq2[j - 1] + aligned_seq2
                j -= 1
            elif j == 0:
                aligned_seq1 = seq1[i - 1] + aligned_seq1
                aligned_seq2 = "-" + aligned_seq2
                i -= 1
            elif traceback[i][j] == 0:
                aligned_seq1 = seq1[i - 1] + aligned_seq1
                aligned_seq2 = seq2[j - 1] + aligned_seq2
                i -= 1
                j -= 1
            elif traceback[i][j] == 1:
                aligned_seq1 = "-" + aligned_seq1
                aligned_seq2 = seq2[j - 1] + aligned_seq2
                j -= 1
            else:
                aligned_seq1 = seq1[i - 1] + aligned_seq1
                aligned_seq2 = "-" + aligned_seq2
                i -= 1

        # Ensure full sequences are returned
        aligned_seq1, aligned_seq2 = cls.restore_full_sequences(
            seq1, seq2, aligned_seq1, aligned_seq2
        )

        return aligned_seq1, aligned_seq2, max_score

    @staticmethod
    def restore_full_sequences(seq1, seq2, aligned_seq1, aligned_seq2):
        start1 = seq1.find(aligned_seq1.replace("-", ""))
        start2 = seq2.find(aligned_seq2.replace("-", ""))

        aligned_seq1 = seq1[:start1] + aligned_seq1
        aligned_seq2 = seq2[:start2] + aligned_seq2

        aligned_seq1 += seq1[start1 + len(aligned_seq1.replace("-", "")) :]
        aligned_seq2 += seq2[start2 + len(aligned_seq2.replace("-", "")) :]

        if len(aligned_seq1) < len(aligned_seq2):
            aligned_seq1 += "-" * (len(aligned_seq2) - len(aligned_seq1))
        if len(aligned_seq2) < len(aligned_seq1):
            aligned_seq2 += "-" * (len(aligned_seq1) - len(aligned_seq2))

        return aligned_seq1, aligned_seq2
