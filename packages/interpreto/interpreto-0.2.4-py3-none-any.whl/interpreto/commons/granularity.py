# MIT License
#
# Copyright (c) 2025 IRT Antoine de Saint Exupéry et Université Paul Sabatier Toulouse III - All
# rights reserved. DEEL and FOR are research programs operated by IVADO, IRT Saint Exupéry,
# CRIAQ and ANITI - https://www.deel.ai/.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""
Definition of different granularity levels for explainers (tokens, words, sentences...)
"""

from __future__ import annotations

from enum import Enum

import torch
from torch.types import Number

from interpreto.typing import HasWordIds, TensorMapping


class NoWordIdsError(AttributeError):
    """
    Exception raised when the word_ids method is not available on the tokenizer
    """

    def __init__(self):
        super().__init__(
            "Word-level granularity level requires tokenization with a fast tokenizer (i.e., tokenizer.is_fast=True), "
            "because it relies on `.word_ids()` to associate tokens with words. "
            "Please either use a fast tokenizer or switch to token-level granularity."
        )


class Granularity(Enum):
    """
    Enumerations of the different granularity levels supported for masking perturbations
    Allows to define token-wise masking, word-wise masking...
    """

    ALL_TOKENS = "all_tokens"  # All tokens, including special tokens like padding, eos, cls, etc.
    TOKEN = "token"  # Strictly tokens of the input
    WORD = "word"  # Words of the input
    DEFAULT = ALL_TOKENS

    @staticmethod
    def __all_tokens_assoc_matrix(tokens_ids: TensorMapping) -> torch.Tensor:
        n, l_p = tokens_ids["input_ids"].shape
        return torch.eye(l_p).unsqueeze(0).expand(n, -1, -1)

    @staticmethod
    def __token_assoc_matrix(tokens_ids: TensorMapping) -> torch.Tensor:
        # TODO : remake this using only tensor operation (if possible ?)
        n, l_p = tokens_ids["input_ids"].shape
        perturbable_matrix = torch.diag_embed(1 - tokens_ids["special_tokens_mask"])
        non_empty_rows_mask = perturbable_matrix.sum(dim=2) != 0
        l_t = non_empty_rows_mask.sum(dim=1)
        result = torch.zeros(n, int(l_t.max().item()), l_p)
        for i in range(n):
            result[i, : l_t[i], :] = perturbable_matrix[i, non_empty_rows_mask[i]]
        return result

    @staticmethod
    def __word_assoc_matrix(tokens_ids: TensorMapping) -> torch.Tensor:
        if not isinstance(tokens_ids, HasWordIds):
            raise NoWordIdsError()
        n = tokens_ids["input_ids"].shape[0]
        l_t = int(Granularity.get_length(tokens_ids, Granularity.WORD).max().item())
        index_tensor = torch.nn.utils.rnn.pad_sequence(
            [
                torch.tensor([a if a is not None else l_t for a in elem])
                for elem in [tokens_ids.word_ids(i) for i in range(n)]
            ],
            batch_first=True,
            padding_value=l_t + 1,
        )
        reference = torch.diagonal_scatter(torch.zeros(l_t + 1, l_t), torch.ones(l_t))
        res = (
            torch.index_select(reference, 0, index_tensor.flatten())
            .reshape(index_tensor.shape + (reference.shape[1],))
            .transpose(-1, -2)
        )
        return res

    @staticmethod
    def get_length(tokens_ids: TensorMapping, granularity: Granularity | None = None) -> torch.Tensor:
        """
        Returns the length of the sequences according to the granularity level

        Args:
            tokens_ids (TensorMapping): tensors to measure
            granularity (Granularity, optional): granularity level. Defaults to DEFAULT.

        Returns:
            torch.Tensor: length of the sequences
        """
        match granularity or Granularity.DEFAULT:
            case Granularity.ALL_TOKENS:
                return tokens_ids["input_ids"].shape[1] * torch.ones(tokens_ids["input_ids"].shape[0])
            case Granularity.TOKEN:
                return (1 - tokens_ids["special_tokens_mask"]).sum(dim=1)
            case Granularity.WORD:
                if not isinstance(tokens_ids, HasWordIds):
                    raise NoWordIdsError()
                return (
                    torch.tensor(
                        [
                            max(a for a in tokens_ids.word_ids(i) if a is not None)
                            for i in range(tokens_ids["input_ids"].shape[0])
                        ]
                    )
                    + 1
                )
            case _:
                raise NotImplementedError(f"Granularity level {granularity} not implemented")

    @staticmethod
    def get_decomposition(tokens_ids: TensorMapping, granularity: Granularity | None = None):
        """Return the token decomposition at the requested granularity level.

        This method groups token ids according to the chosen granularity. It can
        either keep every token, ignore special tokens or merge tokens that
        belong to the same word.

        Args:
            tokens_ids (TensorMapping): Tokenized inputs to decompose.
            granularity (Granularity | None, optional): Desired granularity level. Defaults to
                :attr:`DEFAULT`.

        Returns:
            list[list[list[Number]]]: A nested list where the first level
            indexes the batch elements, the second level corresponds to groups of
            tokens and the last level contains the token ids inside each group.
        """
        match granularity or Granularity.DEFAULT:
            case Granularity.ALL_TOKENS:
                return Granularity.__all_tokens_decomposition(tokens_ids)
            case Granularity.TOKEN:
                return Granularity.__token_decomposition(tokens_ids)
            case Granularity.WORD:
                return Granularity.__word_decomposition(tokens_ids)
            case _:
                raise NotImplementedError(f"Granularity level {granularity} not implemented in decompose function")

    @staticmethod
    def __all_tokens_decomposition(tokens_ids: TensorMapping) -> list[list[list[Number]]]:
        return [[[tok.item()] for tok in seq] for seq in tokens_ids["input_ids"]]

    @staticmethod
    def __token_decomposition(tokens_ids: TensorMapping) -> list[list[list[Number]]]:
        if "special_tokens_mask" not in tokens_ids.keys():
            raise ValueError(
                "Cannot decompose tokens without `'special_tokens_mask'`."
                + "Try to tokenize the input with `return_special_tokens_mask=True`."
            )
        return [
            [[tok.item()] for tok, mask in zip(seq, mask_seq, strict=True) if mask == 0]
            for seq, mask_seq in zip(tokens_ids["input_ids"], tokens_ids["special_tokens_mask"], strict=True)
        ]

    @staticmethod
    def __word_decomposition(tokens_ids: TensorMapping) -> list[list[list[Number]]]:
        if not isinstance(tokens_ids, HasWordIds):
            raise NoWordIdsError()
        res: list[list[list[Number]]] = []
        for index, token_ids in enumerate(tokens_ids["input_ids"]):
            word_ids = tokens_ids.word_ids(index)
            res.append([[] for _ in range(max(a for a in word_ids if a is not None) + 1)])
            for tok, word_id in zip(token_ids, word_ids, strict=True):
                if word_id is not None:
                    res[-1][word_id] += [tok.item()]
        return res

    @staticmethod
    def get_association_matrix(tokens_ids: TensorMapping, granularity: Granularity | None = None) -> torch.Tensor:
        """
        Creates the matrix to pass from one granularity level to ALL_TOKENS granularity level (finally used by the perturbator)


        Args:
            tokens_ids (TensorMapping): inputs of the perturb meth
            granularity (Granularity | None, optional): source granularity level. Defaults to Granularity.DEFAULT.

        Raises:
            NotImplementedError: if granularity level is unknown, raises NotImplementedError

        Returns:
            torch.Tensor: the matrix used to transform a specific granularity mask to a general mask that can be used on tokens
        """
        match granularity or Granularity.DEFAULT:
            case Granularity.ALL_TOKENS:
                return Granularity.__all_tokens_assoc_matrix(tokens_ids)
            case Granularity.TOKEN:
                return Granularity.__token_assoc_matrix(tokens_ids)
            case Granularity.WORD:
                return Granularity.__word_assoc_matrix(tokens_ids)
            case _:
                raise NotImplementedError(f"Granularity level {granularity} not implemented")
