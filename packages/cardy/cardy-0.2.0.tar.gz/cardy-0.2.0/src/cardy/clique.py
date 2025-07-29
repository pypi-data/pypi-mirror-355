# Copyright 2025 Cardy Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from collections.abc import Collection, Mapping
from random import Random

from .distance import distance
from .neighbourhood import neighbourhood
from .types import CardSort, CliqueHeuristic

__all__ = ("Selector", "random_strategy", "greedy_strategy", "clique")


class Selector:
    def __init__(self, seed=None):
        self.random = Random(seed)

    def select[T](self, collection: Collection[T]) -> T:
        """Selects an item from the given collection at random"""
        return self.random.sample(tuple(collection), k=1)[0]


def random_strategy[K, T](
      _: int,
      candidates: Mapping[K, CardSort[T]],
      selector: Selector = Selector(),
) -> K:
    """
    A heuristic strategy to select clique candidates at random.

    :param _: The max distance between any two sorts in the clique
    :param candidates: The intersection of the current clique
        sort neighbourhoods
    :param selector: An object to select an item from a collection at random
    :return: A randomly selected element
    """
    return selector.select(candidates)


def greedy_strategy[K, T](
      d: int,
      candidates: Mapping[K, CardSort[T]],
      selector: Selector = Selector(),
) -> K:
    """
    A heuristic strategy to select candidates from a set of sorts to add to a
    clique. See: <https://doi.org/10.1111/j.1468-0394.2005.00304.x>

    In the case where two or more candidates reduce the candidate pool by the
    same amount, one is chosen at random using the given selector.

    :param d: The max distance between any two sorts in the clique
    :param candidates: The intersection of the current clique
        sort neighbourhoods
    :param selector: An object to select an item from a collection at random
    :return: An element that reduces the clique size by the smallest amount
    """
    current_max = 0
    max_candidates = []
    for key, candidate in candidates.items():
        size = len(neighbourhood(d, candidate, candidates))
        if size > current_max:
            max_candidates = [key]
            current_max = size
        elif size == current_max:
            max_candidates.append(key)
    return selector.select(max_candidates)


def clique[K, T](
      d: int,
      probe: CardSort[T],
      sorts: Mapping[K, CardSort[T]],
      strategy: CliqueHeuristic[T] = greedy_strategy,
) -> set[K]:
    """
    Computes the d-clique centred around the given probe sort using the given
    heuristic strategy.

    The card sorts collection does not need to contain the probe sort. The probe
    sort will not be included in the result in this case.

    The strategy is a heuristic used to select candidate card sorts to add to
    the clique. See <https://doi.org/10.1111/j.1468-0394.2005.00304.x> for more.

    :param d: The max distance between any two sorts in the clique
    :param probe: The starting probe sort
    :param sorts: The collection of card sorts to search for the clique in
    :param strategy: The heuristic strategy for selecting candidates to add to
        the clique.
    :return: A d-clique around the probe sort
    """
    clique_set = {
        key for key, sort in sorts.items() if distance(sort, probe) == 0
    }
    candidates = {
        key: sort for key, sort in sorts.items()
        if 0 < distance(sort, probe) <= d
    }
    while candidates:
        selected = strategy(d, candidates)
        clique_set.add(selected)
        candidates = {
            key: sort for key, sort in candidates.items()
            if key != selected and distance(sort, candidates[selected]) <= d
        }
    return clique_set
