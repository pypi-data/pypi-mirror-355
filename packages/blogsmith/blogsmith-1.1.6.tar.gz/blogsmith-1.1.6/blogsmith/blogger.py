import os
import numpy as np
import networkx as nx
import markdown
import openai
from sentify.segmenter import Segmenter
from vecstore.vecstore import VecStore, normarr

trace = 0
caching = True

API_KEY = [os.getenv("OPENAI_API_KEY")]
GPT_MODEL = ["gpt-4o", "text-embedding-3-small", 1536, "gpt"]

USE_OLLAMA = [False]
OLLAMA_MODEL = ["mistral-nemo:12b", "mxbai-embed-large", 1024, "ollama"]

SKIP_WEBIFY = USE_OLLAMA[0]


def get_llm_name():
    if USE_OLLAMA[0]:
        return OLLAMA_MODEL[3]
    else:
        return GPT_MODEL[3]


def get_client():
    if USE_OLLAMA[0]:
        # Ollama API is OpenAI-compatible (does not check API key)
        return openai.OpenAI(
            base_url="http://u.local:11434/v1",
            # base_url="http://localhost:11434/v1",
            api_key="ollama",  # Ollama ignores the key, but requires it
        )
    else:
        api_key = API_KEY[0]
        return openai.OpenAI(api_key=api_key)


def get_model():
    if USE_OLLAMA[0]:
        return OLLAMA_MODEL[0]
    else:
        return GPT_MODEL[0]


def get_embedding_model():
    if USE_OLLAMA[0]:
        return OLLAMA_MODEL[1]
    else:
        return GPT_MODEL[1]


def get_emb_dim():
    if USE_OLLAMA[0]:
        return OLLAMA_MODEL[2]
    else:
        return GPT_MODEL[2]


def set_openai_api_key(key):
    if API_KEY[0]:
        return API_KEY[0]

    if key and len(key) > 40:
        API_KEY[0] = key
    else:
        key = ""
    return key


def clear_key():
    API_KEY[0] = ""
    os.environ["OPENAI_API_KEY"] = ""


segmenter = Segmenter()


def tprint(*args, **kwargs):
    """Print a trace message if trace is enabled."""
    if trace:
        print(*args, **kwargs)


def try_llm(prompt: str):
    """Try to ask the OpenAI API for a given prompt."""
    client = get_client()
    try:
        response = client.chat.completions.create(
            model=get_model(),
            messages=[{"role": "user", "content": prompt}],
        )
        if response is None:
            print("*** No response from OpenAI API")
            exit(1)
        return response
    except openai.OpenAIError as e:
        print("*** OpenAIError:", e)
        exit(1)


def ask(prompt: str) -> tuple[str, float]:
    """Return the response from the OpenAI API for a given prompt."""

    client = get_client()
    try:
        response = client.chat.completions.create(
            model=get_model(),
            messages=[{"role": "user", "content": prompt}],
        )
        if response is None:
            print("*** No response from OpenAI API")
            exit(1)
    except openai.OpenAIError as e:
        print("*** OpenAIError:", e)
        exit(1)

    if USE_OLLAMA[0]:
        cost = 0.0
    else:
        usage = response.usage
        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens

        input_rate = 0.005 / 1000  # $0.005 per 1K input tokens
        output_rate = 0.015 / 1000  # $0.015 per 1K output tokens

        cost = (input_tokens * input_rate) + (output_tokens * output_rate)

    return response.choices[0].message.content, cost


def ask_and_segment(prompt: str) -> tuple[list[str], float]:
    """Segment into sentences the OpenAI answer for a given prompt."""
    response, cost = ask(prompt)
    response = response.replace('"', " ")
    return segmenter.text2sents(response), cost


def get_embeddings(sents: list[str]) -> list[list[float]]:
    """
    Return the embedding vector for list of sentences using the OpenAI Embedding API.
    """
    model = get_embedding_model()
    client = get_client()
    try:
        response = client.embeddings.create(model=model, input=sents)
    except openai.OpenAIError as e:
        print("*** OpenAIError:", e)
        exit(1)
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


def trim(sents: list[str], keep: float = 0.50) -> list[str]:
    """Trim a list of sentences to keep only the top ranked sentences."""
    n = max(5, int(len(sents) * keep))
    return sents[0:n]


def save_sents(sents: list[str], fname: str):
    """Save sentences to a text file."""

    with open(fname, "w") as f:
        for sent in sents:
            f.write(sent + "\n")


def load_sents(fname: str) -> list[str]:
    """Load sentences from a text file."""
    with open(fname, "r") as f:
        return [line.strip() for line in f.readlines()]


def file_name(topic: str) -> str:
    """Return the name of the file for a given topic."""
    name = topic.replace(" ", "_").lower()
    return f"out/blog_{name}_{get_llm_name()}"


def save_text(text: str, topic: str):
    """Save the text to a file."""

    fname = file_name(topic)
    with open(f"{fname}.txt", "w") as f:
        f.write(text)
    if SKIP_WEBIFY:
        with open(f"{fname}.md", "w") as f:
            f.write(text.replace("**", "\n\n"))


def load_text(topic: str) -> str:
    """Load the text from a file."""
    fname = file_name(topic) + ".txt"
    if not os.path.exists(fname):
        return ""
    with open(fname, "r") as f:
        return f.read()


def save_md(text: str, topic: str):
    """Save the markdown text and html to files."""
    fname = file_name(topic)
    text = text.replace("** ", "\n\n**\n")
    with open(fname + ".md", "w") as f:
        f.write(text)
    with open(fname + ".html", "w") as f:
        html = markdown.markdown(text)
        f.write(html)


def load_md(topic: str) -> str:
    """Load the markdown text from a file."""
    fname = file_name(topic) + ".md"
    if not os.path.exists(fname):
        return ""
    with open(fname, "r") as f:
        return f.read()


class Cache:
    """A cache of embeddings and sentences for a given topic."""

    def __init__(self, name: str, topic: str):
        os.makedirs("cache/", exist_ok=True)
        dim = get_emb_dim()
        llm = get_llm_name()
        tname = topic.replace(" ", "_").lower()
        tname = "cache/" + name.lower() + "_" + tname + "_" + llm
        self.vecstore = VecStore(tname + ".bin", dim=dim)
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
        os.makedirs("out/", exist_ok=True)
        if not caching:
            self.cache.clear()

    # overridable
    def clean_text(self, text: str) -> str:
        """Clean the text, if needed."""
        return text

    def rank_sents(self, sents: list[str]) -> str:
        """Rank and trim the sentences."""

        if len(sents) < 5:
            tprint("\nNot enough sentences to rank:", len(sents))
            return "\n".join(sents)

        kn = max(1, min(len(sents) - 0, 3))

        knns = self.cache.vecstore.all_knns(k=kn, as_weights=False)

        assert (len(knns)) == len(sents), (len(knns), "!=", len(sents))

        ranks = knn_graph(knns)

        ranks = sorted(ranks.items(), key=lambda x: x[1], reverse=True)
        tprint("\nRANKS:", len(sents), "==", len(ranks))
        for x in ranks:
            tprint(x, sents[x[0]])

        # take first k highest ranked, order them by occurence order

        last = len(sents) - 1
        triples = [
            (x[0], x[1], sents[x[0]]) for x in ranks if x[0] != 0 and x[0] != last
        ]
        triples = sorted(triples, key=lambda x: x[1])
        texts = [x[2] for x in triples]
        trimmed_texts = trim(texts, self.keep)

        trimmed_text = "\n".join(trimmed_texts)
        """
        tprint(
            "SUSPECT TEXTS",
            texts,
            "LEN TEXTS:",
            len(texts),
            "LEN TRIMMED:",
            len(trimmed_texts),
        )
        """

        final_text = sents[0] + "\n" + trimmed_text + "\n" + sents[last]
        print("\nSALIENT TRIMMED:", len(trimmed_texts), self.name, "SENTS:", len(sents))
        tprint(final_text)
        return final_text

    def step_no_cache(self):
        """Step without caching."""
        prompt = self.goal

        tprint(f"\n{self.name} PROMPT: {prompt}")
        sents, cost = ask_and_segment(prompt)
        Agent.cost += cost

        if self.keep >= 1.0:
            print(f"SALIENT ALL KEPT\n{self.name} BLOG SENTS: {len(sents)}")
            text = "\n".join(sents)
            return sents, self.clean_text(text)

        embs = get_embeddings(sents)
        tprint("\nNORM:", np.linalg.norm(embs))

        embs = normarr(embs)
        for i, x in enumerate(sents):
            tprint("\n", i, " ----> ", x)
        tprint("\nSHAPE:", embs.shape, "SENTS:", len(sents))
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

        elif self.keep >= 1.0 and output != "":
            print(f"OUTPUT CACHING for {self.name}")
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
        super().__init__(name, prompt, topic, 0.50)


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
        """Save the output to a txt file."""
        tprint("save_output: ", self.name)
        save_text(text, self.topic)

    # override
    def load_output(self) -> str:
        """Load the output from a txt file."""
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

        text = text.replace("\n### ", "\n")
        text = text.replace("#### ", "\n\n#### ")
        text = text.replace("**", " ")
        text = text.replace("!", ":\n\n")
        return text


def init_cost():
    """Initialize the cost of the agents."""
    Agent.cost = 0.0


def get_cost():
    """Get the cost of the agents."""
    return Agent.cost


def run_blogger(topic=None):
    """Run the blogger multi-agent system."""
    print("\n\nSTARTING the blogger on topic: ", topic)
    init_cost()
    assert topic is not None
    intro = BlogStarter("Deep LLM Intro", topic).step()
    details = BlogDetailer("Deep LLM Details", intro, topic).step()
    conclusion = BlogConcluder(
        "Deep LLM Conclusion", intro + "\n\n" + details, topic
    ).step()
    text = "\n\n".join([intro, details, conclusion])
    text = Refiner("Deep LLM Refined", text, topic).step()
    if SKIP_WEBIFY:
        print(f"\n\nCOST:\n{get_cost()}")
        return text

    text = Webifier("Deep LLM in MD form", text, topic).step()

    print(f"\n\nBLOG:\n{text}")
    print(f"\n\nCOST:\n{get_cost()}")

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

    print(f"\n\nCOST: ${get_cost()}")


if __name__ == "__main__":
    test_blogger()
