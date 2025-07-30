import spacy

nlp = spacy.load("en_core_web_sm")

def extract_entities(text):
    doc = nlp(text)
    return list(set([
        ent.text for ent in doc.ents 
        if ent.label_ in ["ORG", "PERSON", "GPE", "MONEY"]
    ]))
