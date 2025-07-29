import os
import numpy as np
import networkx as nx
import markdown
import openai
from sentify.segmenter import Segmenter
from vecstore.vecstore import VecStore, normarr

client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
segmenter = Segmenter()

trace = 0
caching = 1


def tprint(*args, **kwargs):
    """Print a trace message if trace is enabled."""
    if trace:
        print(*args, **kwargs)


def ask(prompt: str):
    """Return the response from the OpenAI API for a given prompt."""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
    )

    usage = response.usage
    input_tokens = usage.prompt_tokens
    output_tokens = usage.completion_tokens

    input_rate = 0.005 / 1000  # $0.005 per 1K input tokens
    output_rate = 0.015 / 1000  # $0.015 per 1K output tokens

    cost = (input_tokens * input_rate) + (output_tokens * output_rate)

    return response.choices[0].message.content, cost


def ask_and_segment(prompt: str) -> list[str]:
    """Segment into sentences the OpenAI answer for a given prompt."""
    response, cost = ask(prompt)
    return segmenter.text2sents(response), cost


def get_embeddings(
    sents: list[str], model: str = "text-embedding-3-small"
) -> list[float]:
    """
    Return the embedding vector for list of sentences using the OpenAI Embedding API.
    """
    response = client.embeddings.create(model=model, input=sents)
    # The API returns a list of data with embeddings.
    embs = [item.embedding for item in response.data]
    return embs


def knn_graph(knns):
    """Return the PageRank of a graph from a list of nearest neighbors."""

    g = nx.DiGraph()

    for i, xs in enumerate(knns):
        for x in xs:
            g.add_edge(i, x[0], weight=1 - x[1])
    rs = nx.pagerank(g)
    return rs


def trim(sents: list[str], keep: float = 0.30) -> list[str]:
    """Trim a list of sentences to keep only the top ranke sentences."""
    n = int(len(sents) * keep)
    return sents[:n]


def save_sents(sents: list[str], fname: str):
    """Save sentences to a text file."""

    with open(fname, "w") as f:
        for sent in sents:
            f.write(sent + "\n")


def load_sents(fname: str) -> list[str]:
    """Load sentences from a text file."""
    with open(fname, "r") as f:
        return [line.strip() for line in f.readlines()]


def save_text(text: str, topic: str):
    """Save the text to a file."""
    name = topic.replace(" ", "_").lower()
    with open(f"out/blog_{name}.txt", "w") as f:
        f.write(text)


def load_text(topic: str) -> str:
    """Load the text from a file."""
    name = topic.replace(" ", "_").lower()
    fname = f"out/blog_{name}.txt"
    if not os.path.exists(fname):
        return ""
    with open(fname, "r") as f:
        return f.read()


def save_md(text: str, topic: str):
    """Save the markdown text to a file."""
    name = topic.replace(" ", "_").lower()
    with open(f"out/blog_{name}.md", "w") as f:
        f.write(text)
    with open(f"out/blog_{name}.html", "w") as f:
        html = markdown.markdown(text)
        f.write(html)


def load_md(topic: str) -> str:
    """Load the markdown text from a file."""
    name = topic.replace(" ", "_").lower()
    fname = f"out/blog_{name}.md"
    if not os.path.exists(fname):
        return ""
    with open(fname, "r") as f:
        return f.read()


class Cache:
    """A cache of embeddings and sentences for a given topic."""

    def __init__(self, name: str, topic: str):
        tname = topic.replace(" ", "_").lower()
        tname = "cache/" + name.lower() + "_" + tname
        self.vecstore = VecStore(tname + ".bin", dim=1536)
        self.sentstore = tname + ".txt"

    def save(self, sents: list[str]):
        """Save to the cache."""
        self.vecstore.save()
        save_sents(sents, self.sentstore)

    def load(self) -> list[str]:
        """Load from the cache."""
        self.vecstore.load()
        return load_sents(self.sentstore)

    def clear(self):
        """Clear the cache."""
        if os.path.exists(self.vecstore.fname):
            os.remove(self.vecstore.fname)
        if os.path.exists(self.sentstore):
            os.remove(self.sentstore)

    def exists(self):
        return os.path.exists(self.vecstore.fname) and os.path.exists(self.sentstore)


class Agent:

    def __init__(self, name: str, goal: str, topic: str, keep: float):
        """Initialize the agent."""
        self.name = name  # Name of the agent.
        self.goal = goal  # Goal of the agent.
        self.keep = keep  # Fraction of sentences to keep.
        self.topic = topic  # Topic of the blog.
        self.cache = Cache(name, topic)
        if not caching:
            self.cache.clear()

    # overridable
    def clean_text(self, text: str) -> str:
        """Clean the text, if needed."""
        return text

    def rank_sents(self, sents: list[str]) -> str:
        """Rank and trim the sentences."""

        knns = self.cache.vecstore.all_knns(k=3, as_weights=False)

        assert (len(knns)) == len(sents), (len(knns), "!=", len(sents))

        ranks = knn_graph(knns)

        ranks = sorted(ranks.items(), key=lambda x: x[1], reverse=True)
        tprint("\nRANKS:", len(sents), "==", len(ranks))
        for x in ranks:
            tprint(x, sents[x[0]])

        # take first k highest ranked, order them by occurence order

        last = len(sents) - 1
        text = [(x[0], sents[x[0]]) for x in ranks if x[0] != 0 and x[0] != last]
        text = sorted(text, key=lambda x: x[0])
        text = trim(text, self.keep)
        text = "\n".join([x[1] for x in text])

        text = sents[0] + "\n" + text + "\n" + sents[last]
        print("\nSALIENT:", self.name, "SENTS:", len(sents))
        tprint(text)
        return text

    def step_no_cache(self):
        """Step without caching."""
        prompt = self.goal

        tprint(f"\n{self.name} PROMPT: {prompt}")
        sents, cost = ask_and_segment(prompt)
        Agent.cost += cost

        if self.keep >= 1.0:
            print(f"SALIENT \n{self.name} BLOG SENTS: {len(sents)}")
            text = "\n".join(sents)
            return sents, self.clean_text(text)

        embs = get_embeddings(sents)
        tprint("\nNORM:", np.linalg.norm(embs))

        embs = normarr(embs)
        for x in sents:
            tprint(x)
        tprint("\nSHAPE:", embs.shape)
        self.cache.vecstore.add(embs)
        self.cache.save(sents)  # also saves the embeddings
        return sents, None

    # overridable
    def save_output(self, text: str):
        tprint("no save_output: ", self.name)

    # overridable
    def load_output(self) -> str:
        tprint("no load_output: ", self.name)
        return ""

    def step_with_cache(self):
        """Step with caching."""
        sents = self.cache.load()
        if len(sents) == 0:
            return self.step_no_cache()
        return sents, None

    def step(self) -> str:
        output = self.load_output()

        if self.cache.exists():
            print(f"CACHE HIT {self.name}")
            # sentences and embeddings loading but eanking needs to be done!
            sents = self.cache.load()
            # ranking will needed also

        elif self.keep == 1.0 and output != "":
            print(f"OTPUT CACHING for {self.name}")
            return output

        else:
            print(f"CACHE MISS {self.name}")
            sents, text = self.step_no_cache()
            # also embeddings now in vector store
            if text is not None:
                self.save_output(text)
                return text
            # otherwise, we need to rank the sentences

        # ranking done for the next iteration !!!
        text = self.rank_sents(sents)
        # text has been trimmed to most salient sentences

        self.save_output(text)
        return text


class BlogStarter(Agent):

    def __init__(self, name: str, topic: str):
        """Initialize the agent with specific prompt."""

        prompt: str = f"""
        You want to write a comprehensive blog post about
        {topic}.
        Start the blog with a few pargraphs motivating why this is important
        and why this is difficult.
        Do not use any markup, enumerations or other formatting. 
        Just clear, plain sentences, please!
        """
        super().__init__(name, prompt, topic, 0.42)


class BlogDetailer(Agent):

    def __init__(self, name: str, goal: str, topic: str):
        """Initialize the agent with specific prompt."""

        prompt = f"""
        You are progressing on your comprehensive blog post about
        {topic}.
        Please elaborate on the details of the blog
        by writing a paragraph on each of the key ideas outlined in:
        
        {goal}.
        
        
        Delve deep into the details of each idea, 
        providing exact technical explanations
        about how it could be implemented.
        
        Do not use any markup, enumerations or other formatting. 
        """
        super().__init__(name, prompt, topic, 0.72)


class BlogConcluder(Agent):

    def __init__(self, name: str, goal: str, topic: str):
        """Initialize the agent with specific prompt."""
        prompt = f"""
        You are concluding your comprehensive blog post about
        {topic}.
        Please conclude  the blog by focusing on
        the significance of the key ideas in:
        
        {goal}.
        
        Do not use any markup, enumerations or other formatting. 
        Just clear, plain sentences, please!
        """
        super().__init__(name, prompt, topic, 0.72)


class Refiner(Agent):

    def __init__(self, name: str, goal: str, topic: str):
        """Initialize the agent with specific prompt."""
        prompt = f"""
        You are refining the draft of your blog post about
        {topic}.
        Please improve the narrative style of the blog and make sure each sentence
        flows naturally:\n\n. 
        Do not use any markup, enumerations or other formatting. 
        Just clear, plain sentences, please!
        \n\n
        Here is the draft of the blog that you will need to refine:
        
        {goal}

        """
        super().__init__(name, prompt, topic, 1.0)

    # override
    def save_output(self, text: str):
        """Save the output to a ftxt ile."""
        tprint("save_output: ", self.name)
        save_text(text, self.topic)

    # override
    def load_output(self) -> str:
        """Load the output from a ftxt ile."""
        tprint("load_output: ", self.name)
        text = load_text(self.topic)
        return text


class Webifier(Agent):

    def __init__(self, name: str, goal: str, topic: str):
        """Initialize the agent with specific prompt."""
        prompt = f"""
        You are reformatting to markdown form the plain text your blog about
        {topic}. 
        
        Please invent a short title, based on {topic}.
        Start the title with ## and end it with two newlines.       
        
        Invent short 5-6 words subtitles for each group of 300-400 words.
        Start each subtitle with #### and end the subtitle  with the ! character
        Then, after the ! character, insert two newlines.
        
        Here is the draft of the blog that you will need to reformat in md form:
        
        {goal}
        """
        super().__init__(name, prompt, topic, 1.0)

    def save_output(self, text: str):
        """Save the output to a md file."""
        tprint("save_output: ", self.name)
        save_md(text, self.topic)

    # override
    def load_output(self) -> str:
        """Load the output from a md file."""
        tprint("load_output: ", self.name)
        return load_md(self.topic)

    # override
    def clean_text(self, text: str) -> str:
        """Override the super method to handle markdown formatting."""

        pref = "```markdown "
        suf = "```"

        if text.startswith(pref) and text.endswith(suf):
            lp = len(pref)
            ls = len(suf)
            text = text[lp : len(text) - ls]

        text = text.replace("####", "\n\n####")
        text = text.replace("!", ":\n\n")
        return text


def run_blogger(topic=None):
    """Run the blogger multi-agent system."""
    print("\n\nSTARTING the blogger on topic: ", topic)
    Agent.cost = 0.0
    assert topic is not None
    intro = BlogStarter("Deep LLM Intro", topic).step()
    details = BlogDetailer("Deep LLM Details", intro, topic).step()
    conclusion = BlogConcluder(
        "Deep LLM Conclusion", intro + "\n\n" + details, topic
    ).step()
    text = "\n\n".join([intro, details, conclusion])
    text = Refiner("Deep LLM Refined", text, topic).step()
    text = Webifier("Deep LLM in MD form", text, topic).step()
    # save_md(text, topic)

    print(f"\n\nBLOG:\n{text}")

    return text


def test_blogger():
    "Test the blogger multi-agent system on several topics."

    genAIlogic = (
        "logic programming tools that improve reasoning in Generative AI models"
    )

    selfLLM = "self-awareness as an enhancer of LLMs capabilities"

    termLimits = "impact of term limits on Congress members on high taxes and pork"

    maxDisney = "getting the best ride experience at Disney World"

    teachLP = "teaching logic programming to high school students"

    rDep = "research fields hopelessly deprecated by today's Generative AI"
    bDep = "startup ideas hopelesly deprecated by today's Generative AI"
    mDep = "machine leaarning fields hopelessly deprecated by today's Generative AI"
    sDep = "symbolic AI fields hopelessly deprecated by today's Generative AI"
    pDep = "professions hopelessly deprecated by today's Generative AI"
    vJev = "how to  legislate us out of the Jevons effect"
    vTaxAI = "what taxes should AI companies pay to compensate creators"
    vAut = "how to get rid of authoritarian regimes"
    superInt = "AI superintelligence requires sound logical reasoning"
    intLog = "intuitionistic logic is the inner logic of LLM generated discourse"
    intSuper = "intuitionistic logic is the inner logic of AI-based superintelligence"
    hornSuper = "Horn clause logic is the inner logic of AI-based superintelligence"

    run_blogger(topic=genAIlogic)
    run_blogger(topic=selfLLM)
    run_blogger(topic=termLimits)
    run_blogger(topic=maxDisney)
    run_blogger(topic=teachLP)
    run_blogger(topic=rDep)
    run_blogger(topic=bDep)
    run_blogger(topic=mDep)
    run_blogger(topic=sDep)
    run_blogger(topic=pDep)

    run_blogger(topic=vJev)
    run_blogger(topic=vTaxAI)
    run_blogger(topic=vAut)

    run_blogger(topic=superInt)
    run_blogger(topic=intLog)
    run_blogger(topic=intSuper)
    run_blogger(topic=hornSuper)

    print(f"\n\nCOST: ${Agent.cost},")


if __name__ == "__main__":
    test_blogger()
