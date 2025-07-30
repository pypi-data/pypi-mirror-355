import re

from dg_sound_fuzz.string import NameMatchHelper


class MatchingRuleEngine:
    MATCHING_THRESHOLD = 0.8

    @staticmethod
    def get_name_matching_score(string_1, string_2, force_version=None):
        force_version = force_version or 2
        if force_version == 2:
            return MatchingRuleEngineV2().get_name_matching_score(string_1, string_2) * 100

        elif force_version == 3:
            return MatchingRuleEngineV3().get_name_matching_score(string_1, string_2) * 100
        return MatchingRuleEngineV1().get_name_matching_score(string_1, string_2)


class MatchingRuleEngineV1:
    MATCHING_THRESHOLD = 0.8

    @staticmethod
    def get_name_matching_score(string_1: str, string_2: str):
        if not all([string_1, string_2]):
            print("[ERROR] Sent blank / null strings for name matching score.")
            return None, None

        if string_1.lower() == string_2.lower():
            return True, 1.0
        helper_obj = NameMatchHelper()
        is_matched, match_score = helper_obj.dg_cv_check_is_matched_for_names(
            helper_obj.dg_cv_filter_employer_name(string_1.lower()),
            helper_obj.dg_cv_filter_employer_name(string_2.lower()),
        )
        match_score -= 0.01
        return is_matched, round(match_score, 1)


def default_name_matching(name1, name2):
    return MatchingRuleEngineV1().get_name_matching_score(name1, name2)


class MatchingRuleEngineV2:
    MATCHING_THRESHOLD = 0.8

    def get_name_matching_score(self, string_1: str, string_2: str) -> float:
        if not all([string_1, string_2]):
            return 0.0

        if not all([isinstance(string_1, str), isinstance(string_2, str)]):
            return 0.0
        # Preprocess the input strings
        string1_cleaned, string2_cleaned = self._preprocess_strings(string_1, string_2)
        if not all([string1_cleaned, string2_cleaned]):
            return 0.0
        # Check for exact match
        if string1_cleaned == string2_cleaned:
            return 1.0

        if sorted(string1_cleaned.split()) == sorted(string2_cleaned.split()):
            return 1.0
        # Apply matching rules
        rule_score, rule_details = self._apply_matching_rules(string1_cleaned, string2_cleaned)
        # Apply reduction rules if necessary
        reduced_score, rule_details = self._apply_reduction_rules(
            string1_cleaned, string2_cleaned, rule_score, rule_details
        )
        return round(reduced_score, 1)

    @staticmethod
    def clean_names(name1: list, name2: list):
        def remove_repeated_words(words: list):
            seen = set()
            cleaned = []
            for word in words:
                if word not in seen or len(word) == 1:
                    seen.add(word)
                    cleaned.append(word)
            return " ".join(cleaned)

        # Clean both names by removing repeated words, but not initials
        cleaned_name1 = remove_repeated_words(name1)
        cleaned_name2 = remove_repeated_words(name2)
        return cleaned_name1, cleaned_name2

    def _preprocess_strings(self, string_1: str, string_2: str):
        name_prefix = ["master", "miss", "mr", "mrs", "ms", "w/o"]

        def clean_and_filter(string):
            words = string.lower().replace(".", " ").split()
            return [word for word in words if word not in name_prefix]

        string1_filtered = clean_and_filter(string_1)
        string2_filtered = clean_and_filter(string_2)
        updated_string_1, updated_string_2 = self.clean_names(string1_filtered, string2_filtered)
        return updated_string_1, updated_string_2

    @staticmethod
    def _apply_matching_rules(string1: str, string2: str):
        helper_obj = NameMatchHelper()
        order_list = [
            ["SC012", "inc_common_names_missing", helper_obj.sc012_common_names],
            ["SC000", "inc_permute_join_matching", helper_obj.sc000_permute_matched],
            ["SC013", "inc_initials_check", helper_obj.sc013_initials_check],
            ["SC014", "inc_soundex_matched", helper_obj.sc014_soundex_matched],
            ["SC015", "3W_2W_one_word_missing", helper_obj.sc015_word_missing],
            ["SC016", "initials_vs_full_name", helper_obj.sc016_initials_vs_full_name],
            ["DEFAULT", "default_code", default_name_matching],
        ]
        score = 0.0

        for rule_code, rule_name, rule_func in order_list:
            _, score = rule_func(string1, string2)
            if score >= 0.8:
                if rule_code == "SC014":
                    _, score = helper_obj.metaphone(string1, string2)
                    if score < 0.8:
                        continue
                return score, (rule_code, rule_name)

        return score, ("DEFAULT", "default_code")

    @staticmethod
    def _apply_reduction_rules(string1, string2, score, rule_details):
        helper_obj = NameMatchHelper()
        if rule_details[0] == "SC016":
            _, red_score = helper_obj.re006_name_gender_check(string1, string2, score)
            if red_score < score:
                return red_score, "dec_name_gender_check"

        if score < MatchingRuleEngineV2.MATCHING_THRESHOLD or rule_details[0] not in ("DEFAULT", "SC014"):
            return score, rule_details[1]

        reduction_list = [
            ["RE002", "dec_initials_check", helper_obj.re002_initials_check],
            ["RE006", "dec_name_gender_check", helper_obj.re006_name_gender_check],
            ["RE001", "dec_soundex_unequal_names", helper_obj.re001_soundex_unequal_names],
            ["RE003", "dec_two_names_vs_one", helper_obj.re003_two_words_vs_one],
            ["RE005", "dec_soundex_single_name", helper_obj.re005_single_name_soundex],
            ["RE010", "dec_is_not_exact_match", helper_obj.re010_is_exact_match],
        ]
        for re_rule_code, re_rule_name, re_rule_func in reduction_list:
            _, reduced_score = re_rule_func(string1, string2, score)
            if reduced_score < score:
                return reduced_score, re_rule_name

        return score, rule_details[1]


class MatchingRuleEngineV3:
    MATCHING_THRESHOLD = 0.8

    @staticmethod
    def get_name_matching_score_v3(string_1: str, string_2: str):
        if not all([string_1, string_2]):
            print("[ERROR] Sent blank / null strings for name matching score.")
            return None, None

        if string_1.lower() == string_2.lower():
            return True, 1.0

        helper_obj = NameMatchHelper()
        is_matched, match_score = helper_obj.dg_cv_check_is_matched_for_names(string_1.lower(), string_2.lower())
        match_score -= 0.01

        return is_matched, round(match_score, 1)

    def get_name_matching_score(self, string_1: str, string_2: str) -> float:
        if not all([string_1, string_2]):
            return 0.0

        if string_1.replace(" ", "").lower() == string_2.replace(" ", "").lower():
            return 1.0

        if not all([isinstance(string_1, str), isinstance(string_2, str)]):
            return 0.0
        # Preprocess the input strings
        string1_cleaned, string2_cleaned = self._preprocess_strings(string_1, string_2)
        if not all([string1_cleaned, string2_cleaned]):
            return 0.0
        # Check for exact match
        if string1_cleaned == string2_cleaned:
            return 1.0
        # Apply matching rules
        rule_score, rule_details = self._apply_matching_rules(string1_cleaned, string2_cleaned)
        # Apply reduction rules if necessary
        reduced_score, _ = self._apply_reduction_rules(string1_cleaned, string2_cleaned, rule_score, rule_details)
        if reduced_score == 1:
            if string_1.replace(" ", "").lower() != string_2.replace(" ", "").lower():
                reduced_score -= 0.1

        return round(reduced_score, 1)

    @staticmethod
    def clean_names(name1: list, name2: list):
        def remove_repeated_words(words: list):
            seen = set()
            cleaned = []
            for word in words:
                if word not in seen or len(word) == 1:
                    seen.add(word)
                    cleaned.append(word)
            return " ".join(cleaned)

        # Clean both names by removing repeated words, but not initials
        cleaned_name1 = remove_repeated_words(name1)
        cleaned_name2 = remove_repeated_words(name2)
        return cleaned_name1, cleaned_name2

    def _preprocess_strings(self, string_1: str, string_2: str):
        def clean_and_filter(string):
            string = re.sub(r"[^\w]", " ", string)
            words = string.replace("  ", " ").lower().split()
            return words

        string1_filtered = clean_and_filter(string_1)
        string2_filtered = clean_and_filter(string_2)
        updated_string_1, updated_string_2 = self.clean_names(string1_filtered, string2_filtered)
        return "".join(updated_string_1), "".join(updated_string_2)

    @staticmethod
    def _apply_matching_rules(string1: str, string2: str):

        helper_obj = NameMatchHelper()
        order_list = [
            ["SC000", "inc_permute_join_matching", helper_obj.sc015_permute_match],
            ["SC013", "inc_initials_check_v3", helper_obj.sc013_initials_check_v3],
            ["SC014", "inc_soundex_matched", helper_obj.sc014_soundex_matched],
            ["SC015", "3W_2W_one_word_missing", helper_obj.sc015_word_missing],
            ["DEFAULT", "default_code", MatchingRuleEngineV3.get_name_matching_score_v3],
        ]

        score = 0.0
        for rule_code, rule_name, rule_func in order_list:
            _, score = rule_func(string1, string2)
            if score >= 0.8:
                return score, (rule_code, rule_name)

        return score, ("DEFAULT", "default_code")

    @staticmethod
    def _apply_reduction_rules(string1, string2, score, rule_details):
        if score < MatchingRuleEngineV2.MATCHING_THRESHOLD or rule_details[0] != "DEFAULT":
            return score, rule_details[1]

        helper_obj = NameMatchHelper()
        reduction_list = [
            ["RE002", "dec_initials_check", helper_obj.re002_initials_check_v3],
            ["RE003", "dec_two_names_vs_one", helper_obj.re003_two_words_vs_one],
            ["RE010", "dec_is_not_exact_match", helper_obj.re010_is_exact_match],
            ["RE008", "dec_unequal_names", helper_obj.re008_dec_unequal_names],
        ]

        for re_rule_code, re_rule_name, re_rule_func in reduction_list:
            _, reduced_score = re_rule_func(string1, string2, score)
            if reduced_score < score:
                return reduced_score, re_rule_name

        return score, rule_details[1]
