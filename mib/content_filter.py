from profanity_filter import ProfanityFilter

pf = ProfanityFilter(languages=['en'])

class ContentFilter:

    @staticmethod
    def censure_content(content):
        
        return pf.censor(content)