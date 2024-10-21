import pytest
import ai_review_app.config as config
from aithena_services.llms.types.message import SystemMessage, UserMessage

from llama_index.core.llms import ChatMessage, ChatResponse, MessageRole

if config.AZURE_OPENAI_AVAILABLE:
    from aithena_services.llms import AzureOpenAI


def prompt_yes():
    return """Always responds 'Yes.' Whatever the user asks, just laconically responds 'Yes.'"""

def prompt_no():
    return """Always responds 'No.' Whatever the user asks, just laconically responds 'No.'"""


PROMPT_SUMMARY = """
You are a research assistant working on a literature review.
Keep a conversational tone.
You are not creative in your responses, you answer user queries based
only on the context provided.
Your only objective is to summarize the documents provided in context.
When doing so, do not cite each document in turn,
but rather provide a cohesive and synthetic summary of all documents at once with proper reference
to doc ids if necessary.
You can however highlights when documents concurs or contradict each other.
You must always describes first the common theme of all documents before diving into any details.

User will provide two pieces of information: [context, query].
Context will be enclosed in XML tags <context>...</context>.
Context will contain documents, each document will follow this format:
<doc>
<doc_id> doc id <doc_id>
<metadata_1>content of metadata 1</metadata_1>
...
<metadata_n>content of metadata n </metadata_n>
<text>Content of the document</text>
</doc>
```
Query will be enclosed in XML tags <query>...</query>.
Query may be empty. If query is not empty, use the content in the query
to guide what type of summary user is looking for.
If query is not relevant to build a sumnmary, ignore it.
Start all your answers with: 'User provided <n> documents.' <n> is the number
of documents in the context.
"""    


@pytest.fixture(scope="session")
def llm():
    return config.LLM_DICT["azure/gpt-4o"]

@pytest.mark.parametrize('repeat', range(5))
def test_custom_system_message(repeat, llm):
    """Test that the system prompt is taken into account on a user interaction."""
    system_message = SystemMessage(content=prompt_yes())
    user_message = UserMessage(content="what is the age of the earth?")
    resp = llm.chat(messages=[system_message.model_dump(), user_message.model_dump()])
    assert resp.message.content == "Yes."
    user_message = UserMessage(content="what is the age of the captain?")
    resp = llm.chat(messages=[system_message.model_dump(), user_message.model_dump()])
    assert resp.message.content == "Yes."

def test_no_user_message(llm):
    """Test that we receive a response just by setting the prompt."""
    system_message = SystemMessage(content=prompt_no())
    resp = llm.chat(messages=[system_message.model_dump()])
    assert resp.message.content == "No."

def test_system_prompt_changed(llm):
    """Test that we can change the system prompt through SystemMessage."""
    system_message = SystemMessage(content=prompt_no())
    resp = llm.chat(messages=[system_message.model_dump()])
    assert resp.message.content == "No."
    system_message = SystemMessage(content=prompt_yes())
    resp = llm.chat(messages=[system_message.model_dump()])
    assert resp.message.content == "Yes."
    print(resp.message.content)

def test_prompt_summary(llm):
    system_message = SystemMessage(content=PROMPT_SUMMARY)
    user_message = UserMessage(content="""
                               <context>
                               <doc><doc_id>doc1<text>Animal are can flying animals, animals that uses their legs, and animal that swims
                               </text></doc>
                               <doc><doc_id>doc2<text>Fishes can live in sea, lakes or rivers.
                                Birds can be on land on leave by the shore and fish for food.
                               Species of birds can eat fish, small mamals or insects. The biggest birds such as the giant eagle can actually eat large animals
                               such as deers or sheep. Those are birds of prey. Other will eat worms or ants. Some will build nest with hay, small
                               branches and other debris, some will nest in tree holes or small excavation in the rock or dirt.
                               </text></doc>
                               <doc><doc_id>doc3<text>Fishes can as short as a millimeters and as long as a 15 stories building. Whales are considered 
                               mammals and are the largest animal leaving underwater. Some have fins, some looks like snakes, some leave in sea water
                               only and some in fresh water. 
                               </text></doc>
                               </content>""")
    resp = llm.chat(messages=[system_message.model_dump(), user_message.model_dump()])
    print(resp.message.content)


wiki_programming_language = """A programming language is a system of notation for writing computer programs.[1]

Programming languages are described in terms of their syntax (form) and semantics (meaning), usually defined by a formal language. Languages usually provide features such as a type system, variables, and mechanisms for error handling. An implementation of a programming language is required in order to execute programs, namely an interpreter or a compiler. An interpreter directly executes the source code, while a compiler produces an executable program.

Computer architecture has strongly influenced the design of programming languages, with the most common type (imperative languages—which implement operations in a specified order) developed to perform well on the popular von Neumann architecture. While early programming languages were closely tied to the hardware, over time they have developed more abstraction to hide implementation details for greater simplicity.

Thousands of programming languages—often classified as imperative, functional, logic, or object-oriented—have been developed for a wide variety of uses. Many aspects of programming language design involve tradeoffs—for example, exception handling simplifies error handling, but at a performance cost. Programming language theory is the subfield of computer science that studies the design, implementation, analysis, characterization, and classification of programming languages.
"""

wiki_python= """Python is a high-level, general-purpose programming language. Its design philosophy emphasizes code readability with the use of significant indentation.[32]

Python is dynamically typed and garbage-collected. It supports multiple programming paradigms, including structured (particularly procedural), object-oriented and functional programming. It is often described as a "batteries included" language due to its comprehensive standard library.[33][34]

Guido van Rossum began working on Python in the late 1980s as a successor to the ABC programming language and first released it in 1991 as Python 0.9.0.[35] Python 2.0 was released in 2000. Python 3.0, released in 2008, was a major revision not completely backward-compatible with earlier versions. Python 2.7.18, released in 2020, was the last release of Python 2.[36]

Python consistently ranks as one of the most popular programming languages, and has gained widespread use in the machine learning community.[37][38][39][40]"""

wiki_c_plus_plus = """
C++ (/ˈsiː plʌs plʌs/, pronounced "C plus plus" and sometimes abbreviated as CPP) is a high-level, general-purpose programming language created by Danish computer scientist Bjarne Stroustrup. First released in 1985 as an extension of the C programming language, it has since expanded significantly over time; as of 1997, C++ has object-oriented, generic, and functional features, in addition to facilities for low-level memory manipulation for systems like microcomputers or to make operating systems like Linux or Windows. It is usually implemented as a compiled language, and many vendors provide C++ compilers, including the Free Software Foundation, LLVM, Microsoft, Intel, Embarcadero, Oracle, and IBM.[14]

C++ was designed with systems programming and embedded, resource-constrained software and large systems in mind, with performance, efficiency, and flexibility of use as its design highlights.[15] C++ has also been found useful in many other contexts, with key strengths being software infrastructure and resource-constrained applications,[15] including desktop applications, video games, servers (e.g., e-commerce, web search, or databases), and performance-critical applications (e.g., telephone switches or space probes).[16]

C++ is standardized by the International Organization for Standardization (ISO), with the latest standard version ratified and published by ISO in December 2020 as ISO/IEC 14882:2020 (informally known as C++20).[17] The C++ programming language was initially standardized in 1998 as ISO/IEC 14882:1998, which was then amended by the C++03, C++11, C++14, and C++17 standards. The current C++20 standard supersedes these with new features and an enlarged standard library. Before the initial standardization in 1998, C++ was developed by Stroustrup at Bell Labs since 1979 as an extension of the C language; he wanted an efficient and flexible language similar to C that also provided high-level features for program organization.[18] Since 2012, C++ has been on a three-year release schedule[19] with C++23 as the next planned standard.[20]
"""

wiki_java = """
Java is a high-level, class-based, object-oriented programming language that is designed to have as few implementation dependencies as possible. It is a general-purpose programming language intended to let programmers write once, run anywhere (WORA),[16] meaning that compiled Java code can run on all platforms that support Java without the need to recompile.[17] Java applications are typically compiled to bytecode that can run on any Java virtual machine (JVM) regardless of the underlying computer architecture. The syntax of Java is similar to C and C++, but has fewer low-level facilities than either of them. The Java runtime provides dynamic capabilities (such as reflection and runtime code modification) that are typically not available in traditional compiled languages.

Java gained popularity shortly after its release, and has been a very popular programming language since then.[18] Java was the third most popular programming language in 2022 according to GitHub.[19] Although still widely popular, there has been a gradual decline in use of Java in recent years with other languages using JVM gaining popularity.[20]

Java was originally developed by James Gosling at Sun Microsystems. It was released in May 1995 as a core component of Sun's Java platform. The original and reference implementation Java compilers, virtual machines, and class libraries were originally released by Sun under proprietary licenses. As of May 2007, in compliance with the specifications of the Java Community Process, Sun had relicensed most of its Java technologies under the GPL-2.0-only license. Oracle offers its own HotSpot Java Virtual Machine, however the official reference implementation is the OpenJDK JVM which is free open-source software and used by most developers and is the default JVM for almost all Linux distributions.

As of March 2024, Java 22 is the latest version. Java 8, 11, 17, and 21 are previous LTS versions still officially supported.
"""

wiki_docs = [wiki_programming_language, wiki_python, wiki_c_plus_plus, wiki_java]
context = [f"""<doc><doc_id>{i}</doc_id><text>{doc}</text></doc>""" for (i, doc) in enumerate(wiki_docs)]
context_string = ("\n").join(context)

def test_prompt_summary_2(llm):
    system_message = SystemMessage(content=PROMPT_SUMMARY)
    user_message = UserMessage(content=f"""<context>{context}</context>""")
    resp = llm.chat(messages=[system_message.model_dump(), user_message.model_dump()])
    print(resp.message.content)


query = """Give a summary of all documents at once."""

def test_prompt_summary_3(llm):
    system_message = SystemMessage(content=PROMPT_SUMMARY)
    user_message = UserMessage(content=f"""<context>{context}</context><query>{query}</query>""")
    resp = llm.chat(messages=[system_message.model_dump(), user_message.model_dump()])
    print(resp.message.content)
