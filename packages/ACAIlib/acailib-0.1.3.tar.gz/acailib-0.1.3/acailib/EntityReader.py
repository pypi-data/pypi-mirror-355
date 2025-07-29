"""Read ACAI data into a dict.

>>> import acailib.EntityReader as er
>>> peoplerd = er.PeopleReader()
# return a list of entities whose preferred label matches a given string
>>> peoplerd.eng_preferred_label_dict["John"]
['person:John.3', 'person:John', 'person:John.2', 'person:John.5', 'person:John.4']
# likewise for other EntityReader subclasses

"""

from collections import UserDict, defaultdict
from collections.abc import Callable
import json
from pathlib import Path
from typing import Optional
from warnings import warn

from acailib import ACAIROOT
from acailib.shared_classes import AcaiDeity, AcaiGroup, AcaiPerson, AcaiPlace


class EntityReader(UserDict):
    """Base class for reading entity data."""

    acaidir: str = ""
    jsondir: Path = Path()
    # typing here needs help
    entryclass: Optional[Callable] = None
    repodata: str = "https://github.com/Clear-Bible/ACAI/tree/main/data"

    def __init__(self, upcase: bool = False) -> None:
        """Initialize an instance.

        With upcase = True (default is False), convert names to all
        upper-case. This is useful for matching TynBD headwords that
        are all upper-case.

        """
        super().__init__()
        assert self.jsondir, "Need to instantiate a subclass of EntityReader"
        for jsonfile in self.jsondir.glob("*.json"):
            with jsonfile.open() as f:
                jdict = json.load(f)
            try:
                if self.entryclass:
                    self.data[jdict["id"]] = self.entryclass(**jdict)
            except Exception as e:
                print(f"Failed on {jsonfile}\n{e}")
        # these are all specific to an entity type for the subclass
        self.eng_preferred_label_dict: defaultdict = defaultdict(list)
        self.eng_alternate_label_dict: defaultdict = defaultdict(list)
        # this is to test for preflabel uniqness
        self._eng_preflabels: set = set()
        self._eng_preflabel_duplicates: defaultdict = defaultdict(list)
        # does not include `key_references`, `explicit_instances`,
        # `pronominal_referents`, or `subject_referents`, so use with
        # caution
        self.references_dict: defaultdict = defaultdict(list)
        for entityid in self.data:
            fullpreflabel: str = self[entityid].localizations["eng"]["preferred_label"]
            # currently about 130 of these that need resolution: should be none
            if fullpreflabel in self._eng_preflabels:
                warn(f"Duplicate preferred label {fullpreflabel} for {entityid}")
                self._eng_preflabel_duplicates[fullpreflabel].append(entityid)
            else:
                self._eng_preflabels.add(fullpreflabel)
            # split is a hack to drop post-name qualifiers
            preflabel = self[entityid].localizations["eng"]["preferred_label"].split(" ")[0]
            altlabels = self[entityid].localizations["eng"].get("alternate_labels", [])
            if upcase:
                preflabel = preflabel.upper()
                altlabels = [label.upper() for label in altlabels]
            self.eng_preferred_label_dict[preflabel].append(entityid)
            for label in altlabels:
                self.eng_alternate_label_dict[label].append(entityid)
            for ref in self[entityid].references:
                self.references_dict[ref].append(entityid)
            # ensure key references are all in the full references list
            # NO: sometimes key references are not in the full references list (e.g., for groups)
            # for keyref in self[entityid].key_references:
            #     if keyref not in self[entityid].references:
            #         warn(f"Key reference {keyref} not in full references list for {entityid}")

    def acai_uri(self, identifier: str) -> str:
        """Return a string for the Github repo location for identifier."""
        nsp, name = identifier.split(":")
        return f"{self.repodata}/{self.acaidir}/json/acai/{name}.json"

    def acai_md_link(self, identifier: str) -> str:
        """Return a Markdown link to the JSON file for identifier."""
        uri = self.acai_uri(identifier)
        return f"[{identifier}]({uri})"

    def references_by_type(self, identifier: str) -> dict[str, list[str]]:
        """Return all the references for an entity, grouped by type."""
        reftypes = [
            # note these overlap with other reference types
            "key_references",
            "references",
            "explicit_instances",
            "pronominal_referents",
            "subject_referents",
        ]
        return {reftype: getattr(self[identifier], reftype) for reftype in reftypes}

    def word_references_by_type(self, identifier: str) -> dict[str, list[str]]:
        """Return all the word-level references for an entity, grouped by type."""
        bcvwpreftypes = [
            "explicit_instances",
            "pronominal_referents",
            "subject_referents",
        ]
        return {
            reftype: references
            for reftype, references in self.references_by_type(identifier).items()
            if reftype in bcvwpreftypes
        }

    def preflabel(self, entityid: str, language: str = "eng") -> str:
        """Return the preferred label for ann entity in the specified language.

        Caveats:
        - Not all preflabels are actually names: occasionally they are
          descriptive terms (e.g. 'Aramitess' for Manasseh's unnamed
          concubine).

        """
        if language != "eng":
            raise NotImplementedError("Not implemented for languages other than English.")
        preflabel: str = self.data[entityid].preflabel(language)
        return preflabel


class DeitiesReader(EntityReader):
    """Read Deities data."""

    acaidir = "deities"
    jsondir = ACAIROOT / acaidir / "json"
    entryclass = AcaiDeity


class GroupsReader(EntityReader):
    """Read Groups data."""

    acaidir = "groups"
    jsondir = ACAIROOT / acaidir / "json"
    entryclass = AcaiGroup


class PeopleReader(EntityReader):
    """Read People data."""

    acaidir = "people"
    jsondir = ACAIROOT / acaidir / "json"
    entryclass = AcaiPerson

    def children_str(self, personid: str, language: str = "eng") -> str:
        """Return a string identifying children."""
        preflabel = self.preflabel(personid, language)
        personinst: AcaiPerson = self.data[personid]
        if personinst.offspring:
            childstr: str = ", ".join(
                [self.data[child].preflabel(language) for child in personinst.offspring]
            )
            if len(childstr) > 1:
                childrenstr = f"children of {preflabel} were"
            else:
                childrenstr = f"child of {preflabel} was"
            return f"The {childrenstr} {childstr}."
        else:
            return ""

    def partner_str(self, personid: str, language: str = "eng") -> str:
        """Return a string identifying partners."""
        preflabel = self.preflabel(personid, language)
        personinst: AcaiPerson = self.data[personid]
        if personinst.partners:
            spousestr: str = ", ".join(
                [self.data[partner].preflabel(language) for partner in personinst.partners]
            )
            if len(spousestr) > 1:
                partnerstr = f"partners of {preflabel} were"
            else:
                partnerstr = f"partner of {preflabel} was"
            return f"The {partnerstr} {spousestr}."
        else:
            return ""


class PlacesReader(EntityReader):
    """Read Places data."""

    acaidir = "places"
    jsondir = ACAIROOT / acaidir / "json"
    entryclass = AcaiPlace


# class FaunaReader(EntityReader):
#     """Read Places data."""

#     acaidir = "fauna"
#     jsondir = ACAIROOT / acaidir / "json"
#     entryclass = AcaiFaunaEntry
