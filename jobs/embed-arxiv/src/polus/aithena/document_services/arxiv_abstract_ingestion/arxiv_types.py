from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from xsdata_pydantic.fields import field

__NAMESPACE__ = "http://arxiv.org/OAI/arXiv/"


class AuthorType(BaseModel):
    class Meta:
        name = "authorType"

    model_config = ConfigDict(defer_build=True)
    keyname: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://arxiv.org/OAI/arXiv/",
            "required": True,
        },
    )
    forenames: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://arxiv.org/OAI/arXiv/",
        },
    )
    suffix: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://arxiv.org/OAI/arXiv/",
        },
    )
    affiliation: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://arxiv.org/OAI/arXiv/",
        },
    )


class AuthorsType(BaseModel):
    class Meta:
        name = "authorsType"

    model_config = ConfigDict(defer_build=True)
    author: list[AuthorType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://arxiv.org/OAI/arXiv/",
            "min_occurs": 1,
        },
    )


class ArXivType(BaseModel):
    class Meta:
        name = "arXivType"

    model_config = ConfigDict(defer_build=True)
    id: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://arxiv.org/OAI/arXiv/",
        },
    )
    created: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://arxiv.org/OAI/arXiv/",
        },
    )
    updated: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://arxiv.org/OAI/arXiv/",
        },
    )
    authors: list[AuthorsType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://arxiv.org/OAI/arXiv/",
        },
    )
    title: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://arxiv.org/OAI/arXiv/",
        },
    )
    msc_class: list[str] = field(
        default_factory=list,
        metadata={
            "name": "msc-class",
            "type": "Element",
            "namespace": "http://arxiv.org/OAI/arXiv/",
        },
    )
    acm_class: list[str] = field(
        default_factory=list,
        metadata={
            "name": "acm-class",
            "type": "Element",
            "namespace": "http://arxiv.org/OAI/arXiv/",
        },
    )
    report_no: list[str] = field(
        default_factory=list,
        metadata={
            "name": "report-no",
            "type": "Element",
            "namespace": "http://arxiv.org/OAI/arXiv/",
        },
    )
    journal_ref: list[str] = field(
        default_factory=list,
        metadata={
            "name": "journal-ref",
            "type": "Element",
            "namespace": "http://arxiv.org/OAI/arXiv/",
        },
    )
    comments: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://arxiv.org/OAI/arXiv/",
        },
    )
    abstract: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://arxiv.org/OAI/arXiv/",
        },
    )
    categories: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://arxiv.org/OAI/arXiv/",
        },
    )
    doi: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://arxiv.org/OAI/arXiv/",
        },
    )
    proxy: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://arxiv.org/OAI/arXiv/",
        },
    )
    license: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://arxiv.org/OAI/arXiv/",
        },
    )


class ArXiv(ArXivType):
    class Meta:
        name = "arXiv"
        namespace = "http://arxiv.org/OAI/arXiv/"

    model_config = ConfigDict(defer_build=True)
