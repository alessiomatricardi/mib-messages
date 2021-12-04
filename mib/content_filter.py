from profanity_filter import ProfanityFilter

pf = ProfanityFilter(languages=['en'])

def censure_content(content):
        
    return pf.censor(content)