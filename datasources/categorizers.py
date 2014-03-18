
__author__ = 'hartsocks'

class Categorizer(object):

    def __init__(self):
        pass

    def category_name(self, identifier):
        pass

    def categorize(self, change):
        pass

class FitnessCategorizer(Categorizer):

    def __init__(self, trusted):
        super(FitnessCategorizer, self).__init__()
        self._trusted = trusted
        self._categories = dict(unknown=-1, revise=0, review=1, core=2, approval=3)
        self._category_list = ['revise', 'review', 'core', 'approval']

    def category_name(self, identifier):
        return self._category_list[identifier]

    @staticmethod
    def has_trusted(voters, trusted):
        for trustee in trusted:
            if trustee in voters:
                return True

    @staticmethod
    def all_trusted(voters, trusted):
        for trustee in trusted:
            if not (trustee in voters):
                return False
        return True

    @staticmethod
    def has_passing_tests(voters):
        ci_systems = ['jenkins', 'vmwareminesweeper']
        return FitnessCategorizer.all_trusted(voters, ci_systems)

    def categorize(self, change):
        trusted = self._trusted
        if not trusted:
            trusted = []

        vote_detail = change.votes

        if 0 < len(vote_detail.get('-2', [])):
            return 'revise'

        if vote_detail.get('-1', []):
            return 'revise'

        category = 1
        if FitnessCategorizer.has_trusted(vote_detail.get('1', []), trusted):
            if FitnessCategorizer.has_passing_tests(vote_detail.get('1', [])):
                if 2 < len(vote_detail.get('1',[])):
                    category = 2
        elif 4 < len(vote_detail.get('1',[])):
            # 2 votes come from jenkins
            category = 2

        if len(vote_detail.get('2', [])):
            category = 3

        return self.category_name(category)