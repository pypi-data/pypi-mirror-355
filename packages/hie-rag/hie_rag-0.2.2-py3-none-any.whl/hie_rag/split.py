import re
from collections import deque
from typing import List, Tuple

from .utils import Utils


class Split:
    def __init__(self, base_url: str = None):
        """
        Initializes the Split object with default or user-defined thresholds.
        """
        self.utils = Utils(base_url=base_url)

    def _custom_split(self, text: str):
        stripped = text.strip()
        # 以「空白行」作為段落切點
        raw_paragraphs = re.split(r'\n\s*\n+', stripped)

        result = []
        for para in raw_paragraphs:
            # 把段落內所有換行改成空格
            single_line = para.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')
            cleaned = single_line.strip()
            if cleaned:
                result.append(cleaned)
        return result

    def _split_large_chunk(self, paragraphs: List[str], embeddings: List[List[float]]) -> (List[str], List[str]):
        """
        Splits 'paragraphs' by finding the least similar boundary using 'embeddings'
        (which are precomputed for these paragraphs only). Returns (left_part, right_part).
        """
        # If there are 0 or 1 paragraphs, no need to split
        if len(paragraphs) < 2:
            return paragraphs, []

        # We'll assume 'embeddings' is already the same length as 'paragraphs'.
        if len(embeddings) < 2:
            # Can't compute consecutive similarities with fewer than 2 embeddings
            return paragraphs, []

        # Find the least similar consecutive boundary
        window_size = 3
        split_index = self.utils.get_windowed_least_similar(embeddings, window_size=window_size)
        
        left_part = paragraphs[:split_index + 1]
        right_part = paragraphs[split_index + 1:]
        return left_part, right_part

    def split(
        self,
        extracted_text: str,
        min_chunk_size: int = 300,
        max_chunk_size: int = 500
    ) -> List[str]:
        
        # 1) Build a deque of triples, so we never mutate three separate lists:
        # paras = [p.strip() for p in extracted_text.split("\n\n") if p.strip()]
        paras = self._custom_split(extracted_text)
        
        if not paras:
            return []

        tokens = [self.utils.count_tokens(p) for p in paras]
        embs   = self.utils.list_embeddings(paras)
        D: deque[Tuple[str,List[float],int]] = deque(
            zip(paras, embs, tokens)
        )

        final_chunks: List[str] = []

        # 2) As long as there’s anything left in D, build one chunk at a time:
        while D:
            cur_paras:    List[str]           = []
            cur_embs:     List[List[float]]   = []
            cur_tokens:   List[int]           = []
            total_tokens = 0

            # 2a) Guarantee we hit at least min_chunk_size
            while D and total_tokens < min_chunk_size:
                p, e, t = D.popleft()
                # if even this one p would bust max, you might choose to take it alone
                if total_tokens + t > max_chunk_size and total_tokens > 0:
                    # push it back for the next round
                    D.appendleft((p,e,t))
                    break
                cur_paras.append(p)
                cur_embs .append(e)
                cur_tokens.append(t)
                total_tokens += t

            # if we ran out before min and have something -> emit it
            if total_tokens < min_chunk_size and not D:
                final_chunks.append(" ".join(cur_paras))
                break

            # 2b) Greedily fill until just under max_chunk_size
            while D and total_tokens + D[0][2] <= max_chunk_size:
                p, e, t = D.popleft()
                cur_paras.append(p)
                cur_embs .append(e)
                cur_tokens.append(t)
                total_tokens += t

            # 3) Now we have between min and max tokens: split at the least-similar boundary
            if cur_paras:
                left, right = self._split_large_chunk(cur_paras, cur_embs)

                # Count tokens in “left” to see if it meets min_chunk_size
                left_token_count = sum(self.utils.count_tokens(p) for p in left)

                if left_token_count >= min_chunk_size:
                    # If left is big enough, emit it
                    final_chunks.append(" ".join(left))

                    # Push “right” (the remainder) back onto D for subsequent chunks
                    for rp, re, rt in reversed(list(zip(
                                    cur_paras[len(left):],
                                    cur_embs  [len(left):],
                                    cur_tokens[len(left):]
                                ))):
                        D.appendleft((rp, re, rt))
                else:
                    # If “left” is too small, just emit the entire cur_paras as one chunk
                    final_chunks.append(" ".join(cur_paras))
                    # (We do NOT push anything back, because cur_paras is fully consumed.)

        return final_chunks 