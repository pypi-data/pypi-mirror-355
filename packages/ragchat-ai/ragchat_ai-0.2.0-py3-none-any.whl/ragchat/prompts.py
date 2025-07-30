from typing import Tuple

from ragchat.definitions import Example, Flow, Language, Prompt, Translations

_entity = Translations(en="entity", es="entidad", fr="entité", de="Entität")
_entities = Translations(en="entities", es="entidades", fr="entités", de="Entitäten")
_fact = Translations(en="fact", es="hecho", fr="fait", de="Fakt")
_facts = Translations(en="facts", es="hechos", fr="faits", de="Fakten")
_chunk = Translations(en="chunk", es="parte", fr="partie", de="Teil")
_chunks = Translations(en="chunks", es="partes", fr="parties", de="Teile")
_is = Translations(en="is", es="es", fr="est", de="ist")
_is_not = Translations(en="is not", es="no es", fr="n'est pas", de="ist nicht")


SUMMARY = Prompt(
    prompt_type="system",
    prompt=Translations(
        en="""
Summarize the INPUT text for semantic search. No explanations, write only the summary.
""",
        es="""
Resume el texto de INPUT para búsqueda semántica. Nada de explicaciones, escribe solo el resumen.
""",
        fr="""
Résumez le texte d'ENTRÉE pour la recherche sémantique. Pas d'explications, écrivez seulement le résumé.
""",
        de="""
Fassen Sie den INPUT-Text für die semantische Suche zusammen. Keine Erklärungen, schreiben Sie nur die Zusammenfassung.
""",
    ),
    examples=[],
)

FACT_ENTITY = Prompt(
    prompt_type="system",
    prompt=Translations(
        en=f"""
Task: Extract facts and entities from the INPUT text.

Instructions:
- Extract important facts, concise and unambiguous
- Extract every entity (i.e. subjects, objects, events, concepts, etc.)
- Entities must be written with format `name (type)`
- No explanations
- Output format:
## {_facts.get(Language.ENGLISH).capitalize()}
- fact

## {_entities.get(Language.ENGLISH).capitalize()}
- name (type)
""",
        es=f"""
Tarea: Extraer todos los temas, hechos y entidades del texto INPUT.

Instrucciones:
- Extrae hechos importantes, concisos y precisos
- Extraer cada entidad (es decir, sujetos, objetos, eventos, conceptos, etc.)
- Las entidades deben escribirse con el formato: 'nombre (tipo)'
- Sin explicaciones
- Formato de salida:
## {_facts.get(Language.SPANISH).capitalize()}
- hecho

## {_entities.get(Language.SPANISH).capitalize()}
- nombre (tipo)
""",
        fr=f"""
Tâche: Extraire les sujets, les faits et les entités du texte INPUT.

Instructions:
- Extraire des sujets concis
- Extraire les faits importants, concis et non ambigus
- Extraire chaque entité (c'est-à-dire sujets, objets, événements, concepts, etc.)
- Les entités doivent être écrites au format `nom (type)`
- Pas d'explications
- Format de sortie:
## {_facts.get(Language.FRENCH).capitalize()}
- fait

## {_entities.get(Language.FRENCH).capitalize()}
- nom (type)
""",
        de=f"""
Aufgabe: Extrahieren Sie Themen, Fakten und Entitäten aus dem INPUT-Text.

Anweisungen:
- Extrahieren Sie prägnante Themen
- Extrahieren Sie wichtige Fakten, prägnant und eindeutig
- Extrahieren Sie jede Entität (d.h. Subjekte, Objekte, Ereignisse, Konzepte usw.)
- Entitäten müssen im Format `Name (Typ)` geschrieben werden
- Keine Erklärungen
- Ausgabeformat:
## {_facts.get(Language.GERMAN).capitalize()}
- Fakt

## {_entities.get(Language.GERMAN).capitalize()}
- Name (Typ)
""",
    ),
    examples=[
        Example(
            flow=Flow.CHAT,
            example_input=Translations(
                en="""
current timestamp: 2023-02-12 13:30

I had dinner with my family last night. My husband cooked lasagna, which is my daughter's favorite dish. Our son brought his girlfriend, who we were meeting for the first time. She brought a lovely bottle of wine that paired perfectly with the meal.
""",
                es="""
current timestamp: 2023-02-12 13:30

Anoche cené con mi familia. Mi esposo cocinó lasaña, que es el plato favorito de mi hija. Nuestro hijo trajo a su novia, a quien conocíamos por primera vez. Ella trajo una botella de vino encantadora que maridó perfectamente con la comida.
""",
                fr="""
current timestamp: 2023-02-12 13:30

J'ai dîné avec ma famille hier soir. Mon mari a cuisiné des lasagnes, qui est le plat préféré de ma fille. Notre fils a amené sa petite amie, que nous rencontrions pour la première fois. Elle a apporté une charmante bouteille de vin qui s'est parfaitement accordée avec le repas.
""",
                de="""
current timestamp: 2023-02-12 13:30

Gestern Abend habe ich mit meiner Familie zu Abend gegessen. Mein Mann hat Lasagne gekocht, das Lieblingsgericht meiner Tochter. Unser Sohn hat seine Freundin mitgebracht, die wir zum ersten Mal trafen. Sie hat eine schöne Flasche Wein mitgebracht, die perfekt zum Essen passte.
""",
            ),
            example_output=Translations(
                en=f"""
## {_facts.get(Language.ENGLISH).capitalize()}
- The user had dinner with the user's family (last night from 2023-02-12 13:30).
- The user's husband cooked lasagna.
- Lasagna is the user's daughter's favorite dish.
- The user's son brought his girlfriend to the family dinner.
- The girlfriend brought a lovely bottle of wine.
- The wine paired perfectly with the meal.
- The user met the user's son's girlfriend (first time).

## {_entities.get(Language.ENGLISH).capitalize()}
- User (current user)
- Family (relatives of user)
- Dinner (event last night from 2023-02-12 13:30)
- Husband (spouse of user)
- Lasagna (Italian pasta dish)
- Daughter (female child of user)
- Son (male child of user)
- Girlfriend (romantic partner of son of user)
""",
                es=f"""
## {_facts.get(Language.SPANISH).capitalize()}
- El usuario/a cenó con su familia (anoche, desde el 12-02-2023 13:30).
- El marido del usuario/a cocinó lasaña.
- La lasaña es el plato favorito de la hija del usuario/a.
- El hijo del usuario/a trajo a su novia a la cena familiar.
- La novia trajo una botella de vino encantadora.
- El vino maridó perfectamente con la comida.
- El usuario/a conoció a la novia de su hijo (primera vez).

## {_entities.get(Language.SPANISH).capitalize()}
- Usuario/a (usuario/a actual)
- Familia (parientes del usuario/a)
- Cena (evento de anoche del 12-02-2023 13:30)
- Marido (cónyuge del usuario/a)
- Lasaña (plato de pasta italiano)
- Hija (hija del usuario/a)
- Hijo (hijo del usuario/a)
- Novia (pareja sentimental del hijo del usuario/a)
""",
                fr=f"""
## {_facts.get(Language.FRENCH).capitalize()}
- L'utilisateur/trice a dîné avec sa famille (hier soir à partir du 12-02-2023 13:30).
- Le mari de l'utilisateur/trice a cuisiné des lasagnes.
- Les lasagnes sont le plat préféré de la fille de l'utilisateur/trice.
- Le fils de l'utilisateur/trice a amené sa petite amie au dîner de famille.
- La petite amie a apporté une charmante bouteille de vin.
- Le vin s'est parfaitement accordé avec le repas.
- L'utilisateur/trice a rencontré la petite amie de son fils (première fois).

## {_entities.get(Language.FRENCH).capitalize()}
- Utilisateur/trice (utilisateur/trice actuel/le)
- Famille (proches de l'utilisateur/trice)
- Dîner (événement d'hier soir du 12-02-2023 13:30)
- Mari (conjoint de l'utilisateur/trice)
- Lasagnes (plat de pâtes italien)
- Fille (enfant de sexe féminin de l'utilisateur/trice)
- Fils (enfant de sexe masculin de l'utilisateur/trice)
- Petite amie (partenaire romantique du fils de l'utilisateur/trice)
""",
                de=f"""
## {_facts.get(Language.GERMAN).capitalize()}
- Der Benutzer/in hat mit seiner Familie zu Abend gegessen (gestern Abend ab 13:30 Uhr am 12.02.2023).
- Der Ehemann des Benutzer/in hat Lasagne gekocht.
- Lasagne ist das Lieblingsgericht der Tochter des Benutzer/in.
- Der Sohn des Benutzer/in hat seine Freundin zum Familienessen mitgebracht.
- Die Freundin hat eine schöne Flasche Wein mitgebracht.
- Der Wein passte perfekt zum Essen.
- Der Benutzer/in hat die Freundin seines/ihres Sohnes getroffen (erstes Mal).

## {_entities.get(Language.GERMAN).capitalize()}
- Benutzer/in (aktueller Benutzer/in)
- Familie (Verwandte des/der Nutzers/in)
- Abendessen (Ereignis von gestern Abend vom 12.02.2023 13:30)
- Ehemann (Ehepartner des/der Nutzers/in)
- Lasagne (italienisches Nudelgericht)
- Tochter (weibliches Kind des/der Nutzers/in)
- Sohn (männliches Kind des/der Nutzers/in)
- Freundin (romantische Partnerin des Sohnes des/der Nutzers/in)
""",
            ),
        ),
        Example(
            flow=Flow.FILE,
            example_input=Translations(
                en="""
source: "Eukaryotes, Origin of". Encyclopedia of Biodiversity. Vol. 2.

Eukaryotic cells, the building blocks of complex life, are thought to have evolved from simpler prokaryotic cells through a process called endosymbiosis, where one prokaryotic cell engulfed another, leading to the development of membrane-bound organelles.
Eukaryotic cells have internal organization with a plasma membrane, cytoplasm containing organelles like mitochondria (energy), endoplasmic reticulum (synthesis), and a nucleus (genetic information) enclosed by a nuclear envelope.
""",
                es="""
fuente: "Eucariotas, Origen de". Enciclopedia de la Biodiversidad. Vol. 2.

Las células eucariotas, los componentes básicos de la vida compleja, se cree que evolucionaron a partir de células procariotas más simples a través de un proceso llamado endosimbiosis, donde una célula procariota engulló a otra, lo que llevó al desarrollo de orgánulos unidos a membranas.
Las células eucariotas tienen organización interna con una membrana plasmática, citoplasma que contiene orgánulos como mitocondrias (energía), retículo endoplasmático (síntesis) y un núcleo (información genética) encerrado por una envoltura nuclear.
""",
                fr="""
source : "Eucaryotes, Origine des". Encyclopédie de la Biodiversité. Vol. 2.

Les cellules eucaryotes, les éléments constitutifs de la vie complexe, sont censées avoir évolué à partir de cellules procaryotes plus simples par un processus appelé endosymbiose, où une cellule procaryote en a englouti une autre, conduisant au développement d'organites liés à une membrane.
Les cellules eucaryotes ont une organisation interne avec une membrane plasmique, un cytoplasme contenant des organites comme les mitochondries (énergie), le réticulum endoplasmique (synthèse) et un noyau (information génétique) entouré d'une enveloppe nucléaire.
""",
                de="""
Quelle: "Eukaryoten, Ursprung der". Enzyklopädie der Biodiversität. Bd. 2.

Eukaryotische Zellen, die Bausteine komplexen Lebens, sollen sich aus einfacheren prokaryotischen Zellen durch einen Prozess namens Endosymbiose entwickelt haben, bei dem eine prokaryotische Zelle eine andere verschlang, was zur Entwicklung membrangebundener Organellen führte.
Eukaryotische Zellen haben eine innere Organisation mit einer Plasmamembran, Zytoplasma, das Organellen wie Mitochondrien (Energie), endoplasmatisches Retikulum (Synthese) und einen von einer Kernhülle umschlossenen Zellkern (genetische Information) enthält.
""",
            ),
            example_output=Translations(
                en=f"""
## {_facts.get(Language.ENGLISH).capitalize()}
- Eukaryotic cells are thought to have evolved from simpler prokaryotic cells through a process called endosymbiosis.
- In endosymbiosis, one prokaryotic cell engulfed another.
- Endosymbiosis led to the development of membrane-bound organelles.
- Eukaryotic cells are the building blocks of complex life.
- Eukaryotic cells have internal organization with a plasma membrane and cytoplasm.
- Cytoplasm contains organelles like mitochondria (energy), endoplasmic reticulum (synthesis) and nucleus (genetic information).
- The nucleus is enclosed by a nuclear envelope.

## {_entities.get(Language.ENGLISH).capitalize()}
- Eukaryotic cells (cell type)
- complex life (concept)
- internal organization (cellular feature)
- Plasma membrane (outer layer of cell)
- Cytoplasm (internal cell fluid)
- organelles (cellular component)
- Mitochondria (energy-producing organelle)
- Endoplasmic reticulum (synthesis organelle)
- Nucleus (genetic information center)
- nuclear envelope (nucleus enclosure)
""",
                es=f"""
## {_facts.get(Language.SPANISH).capitalize()}
- Se cree que las células eucariotas evolucionaron a partir de células procariotas más simples a través de un proceso llamado endosimbiosis.
- En la endosimbiosis, una célula procariota engulló a otra.
- La endosimbiosis condujo al desarrollo de orgánulos unidos a membranas.
- Las células eucariotas son los componentes básicos de la vida compleja.
- Las células eucariotas tienen organización interna con una membrana plasmática y citoplasma.
- El citoplasma contiene orgánulos como mitocondrias (energía), retículo endoplasmático (síntesis) y núcleo (información genética).
- El núcleo está rodeado por una envoltura nuclear.

## {_entities.get(Language.SPANISH).capitalize()}
- Células eucariotas (tipo de célula)
- vida compleja (concepto)
- organización interna (característica celular)
- Membrana plasmática (capa externa de la célula)
- Citoplasma (fluido celular interno)
- orgánulos (componente celular)
- Mitocondrias (orgánulo productor de energía)
- Retículo endoplasmático (orgánulo de síntesis)
- Núcleo (centro de información genética)
- envoltura nuclear (recinto del núcleo)
""",
                fr=f"""
## {_facts.get(Language.FRENCH).capitalize()}
- On pense que les cellules eucaryotes ont évolué à partir de cellules procaryotes plus simples par un processus appelé endosymbiose.
- Dans l'endosymbiose, une cellule procaryote en a englouti une autre.
- L'endosymbiose a conduit au développement d'organites liés à des membranes.
- Les cellules eucaryotes sont les éléments constitutifs de la vie complexe.
- Les cellules eucaryotes ont une organisation interne avec une membrane plasmique et un cytoplasme.
- Le cytoplasme contient des organites comme les mitochondries (énergie), le réticulum endoplasmique (synthèse) et le noyau (information génétique).
- Le noyau est entouré d'une enveloppe nucléaire.

## {_entities.get(Language.FRENCH).capitalize()}
- Cellules eucaryotes (type de cellule)
- vie complexe (concept)
- organisation interne (caractéristique cellulaire)
- Membrane plasmique (couche externe de la cellule)
- Cytoplasme (fluide cellulaire interne)
- organites (composant cellulaire)
- Mitochondries (organite producteur d'énergie)
- Réticulum endoplasmique (organite de synthèse)
- Noyau (centre d'information génétique)
- enveloppe nucléaire (enceinte du noyau)
""",
                de=f"""
## {_facts.get(Language.GERMAN).capitalize()}
- Es wird angenommen, dass sich eukaryotische Zellen aus einfacheren prokaryotischen Zellen durch einen Prozess namens Endosymbiose entwickelt haben.
- Bei der Endosymbiose verschlang eine prokaryotische Zelle eine andere.
- Die Endosymbiose führte zur Entwicklung von membranumschlossenen Organellen.
- Eukaryotische Zellen sind die Bausteine komplexen Lebens.
- Eukaryotische Zellen haben eine innere Organisation mit einer Plasmamembran und Zytoplasma.
- Das Zytoplasma enthält Organellen wie Mitochondrien (Energie), Endoplasmatisches Retikulum (Synthese) und den Zellkern (genetische Information).
- Der Zellkern ist von einer Kernhülle umschlossen.

## {_entities.get(Language.GERMAN).capitalize()}
- Eukaryotische Zellen (Zelltyp)
- komplexes Leben (Konzept)
- innere Organisation (zelluläres Merkmal)
- Plasmamembran (äußere Zellschicht)
- Zytoplasma (innere Zellflüssigkeit)
- Organellen (zellulärer Bestandteil)
- Mitochondrien (energieproduzierende Organelle)
- Endoplasmatisches Retikulum (Synthese-Organelle)
- Zellkern (Zentrum genetischer Information)
- Kernhülle (Umschließung des Zellkerns)
""",
            ),
        ),
    ],
)

RETRIEVAL_CHAT = Prompt(
    prompt_type="system",
    prompt=Translations(
        en="""
You are a helpful assistant. Memories are your own recollections. Use only relevant memories to inform your responses.
""",
        es="""
Eres un asistente útil. Los recuerdos son tus propias rememoraciones. Utiliza solo recuerdos relevantes para informar tus respuestas.
""",
        fr="""
Vous êtes un assistant utile. Les souvenirs sont vos propres souvenirs. Utilisez uniquement les souvenirs pertinents pour éclairer vos réponses.
""",
        de="""
Sie sind ein hilfreicher Assistent. Erinnerungen sind Ihre eigenen Erinnerungen. Verwenden Sie nur relevante Erinnerungen, um Ihre Antworten zu informieren.
""",
    ),
    examples=[],
)

RETRIEVAL_RAG = Prompt(
    prompt_type="user",
    prompt=Translations(
        en="""
Task: Respond to the user query using the provided sources.

Instructions:
- Use only relevant sources to infer the answer
- Incorporate inline citations in brackets: [id]
- Citation ids must correspond to the ids in the source tags `<source id=*>`
- If uncertain, concisely ask the user to rephrase the question to see if you can get better sources
""",
        es="""
Tarea: Responder a la consulta del usuario utilizando las fuentes proporcionadas.

Instrucciones:
- Utiliza solo fuentes relevantes para informar tus respuestas
- Incorpora citas en línea entre corchetes: [id]
- Los ids de las citas deben corresponder a los ids en las etiquetas de fuente `<source id=*>`
- Si no estás seguro, pide concisamente al usuario que reformule la pregunta para ver si puedes obtener mejores fuentes
""",
        fr="""
Tâche : Répondre à la requête de l'utilisateur en utilisant les sources fournies.

Instructions :
- Utilisez uniquement les sources pertinentes pour éclairer vos réponses
- Intégrez des citations en ligne entre crochets : [id]
- Les identifiants de citation doivent correspondre aux identifiants dans les balises source `<source id=*>`
- En cas d'incertitude, demandez de manière concise à l'utilisateur de reformuler la question pour voir si vous pouvez obtenir de meilleures sources
""",
        de="""
Aufgabe: Beantworten Sie die Benutzeranfrage anhand der bereitgestellten Quellen.

Anweisungen:
- Verwenden Sie nur relevante Quellen, um Ihre Antworten zu gestalten
- Fügen Sie Inline-Zitate in Klammern ein: [id]
- Die Zitat-IDs müssen mit den IDs in den Quell-Tags `<source id=*>` übereinstimmen
- Wenn Sie unsicher sind, bitten Sie den Benutzer prägnant, die Frage neu zu formulieren, um zu sehen, ob Sie bessere Quellen erhalten können
""",
    ),
    examples=[
        Example(
            flow=Flow.FILE,
            example_input=Translations(
                en="""
<query>
What were the findings of the study on kv cache?
</query>

<source id="1">
Instead of predicting one token at a time, DeepSeek employs MTP, allowing the model to predict multiple future tokens in a single step.
6</source>
<source id="2">
Red Hat's blog post on integrating DeepSeek models with vLLM 0.7.1 highlights that MLA offers up to 9.6x more memory capacity for key-value (KV) caches.
11</source>
""",
                es="""
<query>
¿Cuáles fueron los hallazgos del estudio sobre la caché KV?
</query>

<source id="1">
En lugar de predecir un token a la vez, DeepSeek emplea MTP, lo que permite al modelo predecir múltiples tokens futuros en un solo paso.
6</source>
<source id="2">
La publicación del blog de Red Hat sobre la integración de los modelos DeepSeek con vLLM 0.7.1 destaca que MLA ofrece hasta 9,6 veces más capacidad de memoria para las cachés de clave-valor (KV).
11</source>
""",
                fr="""
<query>
Quelles ont été les conclusions de l'étude sur le cache KV ?
</query>

<source id="1">
Au lieu de prédire un token à la fois, DeepSeek utilise MTP, permettant au modèle de prédire plusieurs tokens futurs en une seule étape.
6</source>
<source id="2">
L'article de blog de Red Hat sur l'intégration des modèles DeepSeek avec vLLM 0.7.1 souligne que MLA offre jusqu'à 9,6 fois plus de capacité mémoire pour les caches clé-valeur (KV).
11</source>
""",
                de="""
<query>
Was waren die Ergebnisse der Studie zum KV-Cache?
</query>

<source id="1">
Anstatt ein Token nach dem anderen vorherzusagen, verwendet DeepSeek MTP, wodurch das Modell mehrere zukünftige Tokens in einem einzigen Schritt vorhersagen kann.
6</source>
<source id="2">
Der Blogbeitrag von Red Hat zur Integration von DeepSeek-Modellen mit vLLM 0.7.1 hebt hervor, dass MLA bis zu 9,6x mehr Speicherkapazität für Key-Value (KV)-Caches bietet.
11</source>
""",
            ),
            example_output=Translations(
                en="""
According to Red Hat's blog post on integrating DeepSeek models, MLA offers up to 9.6x more memory capacity for key-value caches [2].
""",
                es="""
Según la publicación del blog de Red Hat sobre la integración de modelos DeepSeek, MLA ofrece hasta 9,6 veces más capacidad de memoria para cachés de clave-valor [2].
""",
                fr="""
Selon l'article de blog de Red Hat sur l'intégration des modèles DeepSeek, MLA offre jusqu'à 9,6 fois plus de capacité mémoire pour les caches clé-valeur [2].
""",
                de="""
Laut dem Blogbeitrag von Red Hat zur Integration von DeepSeek-Modellen bietet MLA bis zu 9,6-mal mehr Speicherkapazität für Schlüssel-Wert-Caches [2].
""",
            ),
        ),
    ],
)


MSG_CLASSIFICATION = Prompt(
    prompt_type="system",
    prompt=Translations(
        en="""
Task: Classify the INPUT as 'statement', 'question', 'none'.

Definitions:
- statement: A declaration, assertion or instruction.
- question: An interrogative message seeking information.
- none: The input is incoherent, empty or does not fit into any category.

Instructions:
- Don't answer questions or provide explanations, just classify the message.
- Write 'statement' or 'question' or 'none'
""",
        es="""
Tarea: Clasifica la ENTRADA como 'statement', 'question' o 'none'.

Definiciones:
- statement: Una declaración, afirmación o instrucción.
- question: Un mensaje interrogativo que busca información.
- none: La entrada es incoherente, está vacía o no encaja en ninguna categoría.

Instrucciones:
- No respondas preguntas ni des explicaciones, solo clasifica el mensaje.
- Escribe 'statement' o 'question' o 'none'
""",
        fr="""
Tâche : Classifier l'ENTRÉE comme 'statement', 'question' ou 'none'.

Définitions :
- statement : Une déclaration, une affirmation ou une instruction.
- question : Un message interrogatif cherchant à obtenir des informations.
- none : L'entrée est incohérente, vide ou ne correspond à aucune catégorie.

Instructions :
- Ne répondez pas aux questions et ne donnez pas d'explications, classez simplement le message.
- Écrivez 'statement', 'question' ou 'none'
""",
        de="""
Aufgabe: Klassifiziere die EINGABE als 'statement', 'question' oder 'none'.

Definitionen:
- statement: Eine Aussage, Behauptung oder Anweisung.
- question: Eine Frage, die nach Informationen sucht.
- none: Die Eingabe ist unzusammenhängend, leer oder passt in keine Kategorie.

Anweisungen:
- Beantworte keine Fragen und gib keine Erklärungen, sondern klassifiziere nur die Nachricht.
- Schreibe 'statement', 'question' oder 'none'
""",
    ),
    examples=[
        Example(
            flow=Flow.CHAT,
            example_input=Translations(
                en="""Is it true that the Kingdom of Italy was proclaimed in 1861, while the French Third Republic was established in 1870 and therefore Italy is technically older?""",
                es="""¿Es cierto que el Reino de Italia fue proclamado en 1861, mientras que la Tercera República Francesa se estableció en 1870 y por lo tanto Italia es técnicamente más antigua?""",
                fr=""""Est-il vrai que le Royaume d'Italie a été proclamé en 1861, tandis que la Troisième République française a été établie en 1870 et que l'Italie est donc techniquement plus ancienne?""",
                de="""Stimmt es, dass das Königreich Italien 1861 ausgerufen wurde, während die Dritte Französische Republik 1870 gegründet wurde und Italien somit technisch älter ist?""",
            ),
            example_output=Translations(
                en="question",
                es="question",
                fr="question",
                de="question",
            ),
        ),
        Example(
            flow=Flow.CHAT,
            example_input=Translations(
                en="""Paris is the capital of France. Rome is the capital of Italy.""",
                es="""París es la capital de Francia. Roma es la capital de Italia.""",
                fr=""""Paris est la capitale de la France. Rome est la capitale de l'Italie.""",
                de="""Paris ist die Hauptstadt Frankreichs. Rom ist die Hauptstadt Italiens.""",
            ),
            example_output=Translations(
                en="statement",
                es="statement",
                fr="statement",
                de="statement",
            ),
        ),
        Example(
            flow=Flow.CHAT,
            example_input=Translations(
                en="""Florp wizzlebop cronkulated the splonk! Zizzleflap {}[]()<>:;"/|,.<>? drumblesquanch, but only if the quibberflitz jibberflops. Blorp???""",
                es="""¡Florp wizzlebop cronkuleó el splonk! ¡Zizzleflap {}[]()<>:;"/|,.<>? drumblecuancha, pero solo si el quibberflitz jibberflops! ¡Blorp???""",
                fr="""Florp wizzlebop a cronkulé le splonk ! Zizzleflap {}[]()<>:;"/|,.<>? drumblecuancha, mais seulement si le quibberflitz jibberflops. Blorp ???""",
                de="""Florp wizzlebop hat den Splonk cronkuliert! Zizzleflap {}[]()<>:;"/|,.<>? drumblecuancha, aber nur wenn der quibberflitz jibberflops. Blorp???""",
            ),
            example_output=Translations(
                en="none",
                es="none",
                fr="none",
                de="none",
            ),
        ),
    ],
)


### FORMAT ###

FORMAT = Prompt(
    prompt_type="system",
    prompt=Translations(
        en="""
""",
        es="""
""",
        fr="""
""",
        de="""
""",
    ),
    examples=[
        Example(
            flow=Flow.CHAT,
            example_input=Translations(
                en="""
""",
                es="""
""",
                fr="""
""",
                de="""
""",
            ),
            example_output=Translations(
                en="""
""",
                es="""
""",
                fr="""
""",
                de="""
""",
            ),
        ),
        Example(
            flow=Flow.FILE,
            example_input=Translations(
                en="""
""",
                es="""
""",
                fr="""
""",
                de="""
""",
            ),
            example_output=Translations(
                en="""
""",
                es="""
""",
                fr="""
""",
                de="""
""",
            ),
        ),
    ],
)


def get_equivalence(e1: str, e2: str, lan: Language) -> Tuple[str, str]:
    is_str = _is.get(lan)
    is_not_str = _is_not.get(lan)

    positive_equivalence = f"{e1} {is_str} {e2}"
    negative_equivalence = f"{e1} {is_not_str} {e2}"

    return (positive_equivalence, negative_equivalence)
