import math
import re
from metaphone import doublemetaphone

from rapidfuzz import fuzz

common_surnames = ["bhai", "kumar", "rao", "das", "lal", "iyer"]


def soundex(x):
    x = x.lower()
    if len(re.sub("[aeioyuhw]", "", x)) <= 2:
        return x
    first_char = x[0]
    temp = x[1:]
    temp = re.sub("[aeioyuhw]", "", temp)
    if len(temp) == 0:
        temp = first_char + "000"
        return temp
    else:
        temp = re.sub("[bfpv]", "1", temp)
        temp = re.sub("[cgkq]", "2", temp)
        temp = re.sub("[dt]", "3", temp)
        temp = re.sub("[l]", "4", temp)
        temp = re.sub("[m]", "5", temp)
        temp = re.sub("[jz]", "6", temp)
        temp = re.sub("[n]", "7", temp)
        temp = re.sub("[sx]", "8", temp)
        temp = re.sub("[r]", "9", temp)

        temp = x[0] + temp
        temp = "".join(temp)
        if len(temp) < 4:
            temp += "0" * (4 - len(temp))
        return temp


class NameMatchHelper:

    @staticmethod
    def compare_name(name1_list, name2_list, common_name):
        name1_sorted_list = sorted(name1_list)
        name2_sorted_list = sorted(name2_list)
        is_same = False
        for i in range(0, len(name1_sorted_list)):
            if name1_sorted_list[i] == name2_sorted_list[i]:
                is_same = True
            elif (
                name1_sorted_list[i] + common_name == name2_sorted_list[i]
                or name2_sorted_list[i] + common_name == name1_sorted_list[i]
            ):
                is_same = True
            else:
                is_same = False
                return is_same, 0.0

        return is_same, 0.8

    @staticmethod
    def metaphone(name1, name2):
        meta_name1 = doublemetaphone(name1)
        meta_name2 = doublemetaphone(name2)
        if meta_name1[0] == meta_name2[0]:
            return True, 0.8
        return False, 0.0

    @staticmethod
    def check_only_vowel(name1, name2):
        return name1.replace(name2, "") in {"a", "i"} or name2.replace(name1, "") in {"a", "i"}

    @staticmethod
    def check_input_name_in_website_name(name_1, name_2):
        list_name_split_by_space = name_1.split()

        is_all_words_matching = True
        for word_in_name in list_name_split_by_space:
            if word_in_name not in name_2:
                is_all_words_matching = False
                break

        return is_all_words_matching

    @staticmethod
    def get_unmatched_single_char_scoring(input_unmatched_words, unmatched_words):
        """
        Calculating score for sort names
        e.g. like 'Raj Kapoor and Raj k' or  'Vishwa k and Vishwa Kumar'

        :param input_unmatched_words:
        :param unmatched_words:
        :return:
        """
        try:
            input_unmatched_words.sort()
            unmatched_words.sort()
            single_char_matched_count = 0
            for k, v in enumerate(input_unmatched_words):
                try:
                    if (v == unmatched_words[k][0]) or (unmatched_words[k] == v[0]):
                        single_char_matched_count += 1
                except Exception:
                    pass

            if single_char_matched_count == len(input_unmatched_words):
                return 90
            if single_char_matched_count == 0:
                score_output = 40
            else:
                score_output = 80
            return score_output
        except Exception as err:
            print(f"Exception Error in get_unmatched_single_char_scoring : {err}")
        return 0

    def process_matched_name_with_first_letter_match(self, input_name, emp_name):
        score_output = 0
        input_request_list = input_name.split(" ")
        resp_list = emp_name.split(" ")

        # this is for calculating initials if name containing single chars
        unmatched_words = list(set(resp_list) - set(input_request_list))
        input_unmatched_words = list(set(input_request_list) - set(resp_list))
        unmatched_words.sort()
        input_unmatched_words.sort()
        if len(unmatched_words) == len(input_unmatched_words):
            if len(input_unmatched_words) > 0:
                single_char_scoring = self.get_unmatched_single_char_scoring(input_unmatched_words, unmatched_words)
                if single_char_scoring > 80:
                    score_output = single_char_scoring
                else:
                    score_output = 40
            else:
                score_output = 90

        return score_output

    def dg_cv_check_is_matched_for_names(self, input_name, dg_response_name, allow_retry=True):
        is_matched = False
        sort_ratio = fuzz.token_sort_ratio(input_name, dg_response_name)
        set_ratio = fuzz.token_set_ratio(input_name, dg_response_name)
        temp_score = (sort_ratio + set_ratio) / 2
        base_score = 41
        if input_name.replace(" ", "") == dg_response_name.replace(" ", ""):
            return True, 1.0

        if temp_score > 80:
            score_output = self.process_matched_name_with_first_letter_match(
                str(input_name).lower(), str(dg_response_name).lower()
            )

            if score_output == 40 and temp_score < 95:
                update_score = (base_score + temp_score) // 2
                temp_score = update_score

        if input_name:
            if temp_score > 80 or dg_response_name.startswith(input_name) or input_name.startswith(dg_response_name):
                is_matched = True

        match_score = round(temp_score / 100, 2)
        if not is_matched and match_score < 0.8 and allow_retry:
            is_matched, match_score = self.dg_cv_check_is_matched_for_names(
                input_name.replace(" ", ""), dg_response_name.replace(" ", ""), False
            )

        if match_score == 1:
            total_num_of_spaces = (input_name.count(" ") + dg_response_name.count(" ")) or 0.256
            space_weight = 0.2 * (input_name.count(" ") / total_num_of_spaces)
            match_score -= space_weight

        return is_matched, round(match_score, 2)

    @staticmethod
    def dg_cv_filter_employer_name(company_name):
        prefix_names = ["limited", "ltd", "ltd.", "private", "pvt", "pvt.", "co", "co.", "company", "pvt.ltd"]

        company_name_list = company_name.split(" ")

        for common_name in prefix_names:
            if common_name in company_name_list:
                company_name = str(company_name).replace(common_name, "").strip()

        return company_name.strip()

    @staticmethod
    def sc000_permute_matched(input_name, dg_response_name):
        """
        calculate score for joined but same names
        e.g. "Jakeerhussain Shaik" and "SHAIK JAKEER HUSSAIN"
        """
        try:
            is_matched = False
            score_output = 0.0
            name1 = input_name
            name2 = dg_response_name
            name1_list = input_name.split()
            name2_list = dg_response_name.split()
            lhs = [x for x in name1_list if x]
            rhs = [x for x in name2_list if x]
            if not len(lhs) - len(rhs):
                return is_matched, score_output
            if len(rhs) > len(lhs):
                lhs = name2_list
                rhs = name1_list
                name1 = " ".join(lhs)
                name2 = " ".join(rhs)
            for i in range(0, len(lhs)):
                if name2.find(lhs[i]) != -1:
                    name2 = name2.replace(lhs[i], "")
                    name1 = name1.replace(lhs[i], "")
            if name2.isspace() and name1.isspace():
                is_matched = True
                score_output = 0.8
                return is_matched, score_output
            if name1.strip() and name2.strip() and soundex(name1.strip()) == soundex(name2.strip()):
                is_matched = True
                score_output = 0.8
                return is_matched, score_output

            return is_matched, score_output

        except Exception as err:
            print(f"Exception happens while score calculation and error is : {err}")

    @staticmethod
    def sc015_permute_match(input_name, dg_response_name):
        """
        Check if each word of name is present in one another - LHS and RHS.
        If exact - return 1
        If not exact -
            Partial Match - return 0.8
            No Match - return 0.0
        """
        try:
            lhs = input_name.split()
            rhs = dg_response_name.split()
            lhs_matches, rhs_matches = [], []
            if input_name == dg_response_name:
                return True, 1.0
            for word in lhs:
                if word in dg_response_name:
                    lhs_matches.append(word)
            for word in rhs:
                if word in input_name:
                    rhs_matches.append(word)
            score_output = 0
            if dg_response_name[:3] == "".join(lhs)[:3] or input_name[:3] == "".join(rhs)[:3]:
                total_word_length = len(lhs) + len(rhs)
                score_output = (len(lhs_matches) + len(rhs_matches)) / total_word_length
            return score_output > 0.5, round(score_output, 1)

        except Exception:
            print("Error occurred in SC015_permute_match")

    def sc012_common_names(self, input_name, dg_response_name):
        """
        calculate score for names with common surnames
        common_names like "bhai", "kumar", "rao"
        eg . "Tushar Parmar" and "Parmar Tusharbhai"
        """
        try:
            is_matched = False
            score_output = 0.0

            name1_list = input_name.split(" ")
            name2_list = dg_response_name.split(" ")

            if len(name2_list) != len(name1_list):
                return is_matched, score_output

            for i in common_surnames:
                if input_name.count(i) - dg_response_name.count(i):
                    is_matched, score_output = self.compare_name(name1_list, name2_list, i)

            return is_matched, score_output

        except Exception as err:
            print(f"Exception happens while score calculation and error is : {err}")
            return None

    @staticmethod
    def sc013_initials_check(input_name, response_name):
        """
        Check initials and calculate score.
        """
        try:
            name1_set = set(input_name.split())
            name2_set = set(response_name.split())
            no_match_1 = name1_set - name2_set
            no_match_2 = name2_set - name1_set
            if not any(len(word) == 1 for word in name1_set) and not any(len(word) == 1 for word in name2_set):
                return False, 0.0

            initials1 = [i for i in no_match_1 if len(i) == 1]
            initials2 = [i for i in no_match_2 if len(i) == 1]
            if (len(initials1) == 1 and len(initials2) == 1) and initials1[0] != initials2[0]:
                return False, 0.0

            if all(len(word) == 1 for word in name1_set) or all(len(word) == 1 for word in name2_set):
                return False, 0.0

            if not no_match_1 or not no_match_2:
                return False, 0.0

            if len(no_match_1) != len(no_match_2):
                return False, 0.5 if name1_set & name2_set else 0.4  # Partial match

            if no_match_1 == name1_set or no_match_2 == name2_set:
                return False, 0.0
            match_count, uncertainties, mismatched = 0, 0, 0
            for word1, word2 in zip(sorted(no_match_1), sorted(no_match_2)):
                if word1[0] == word2[0] and (len(word1) == 1 or len(word2) == 1):
                    match_count += 1
                    uncertainties += len(word1) == 1 or len(word2) == 1
                else:
                    mismatched += 1
                    break

            if mismatched > 0:
                return False, 0.0

            if match_count >= 2:
                return True, 0.9 if uncertainties <= 1 else 0.8
            return False, 0.5 if uncertainties <= 1 else 0.4

        except Exception as err:
            print(f"Error in sc013_initials_check: {err}")
            return False, 0.0

    @staticmethod
    def sc013_initials_check_v3(input_name, response_name):
        """
        Check initials and calculate score.
        """
        try:
            name1_set = set(input_name.split())
            name2_set = set(response_name.split())
            no_match_1 = name1_set - name2_set
            no_match_2 = name2_set - name1_set
            if not no_match_1 or not no_match_2:
                return False, 0.0

            if len(no_match_1) != len(no_match_2):
                return False, 0.5 if name1_set & name2_set else 0.4  # Partial match

            if no_match_1 == name1_set or no_match_2 == name2_set:
                return False, 0.0

            match_count, uncertainties, mismatched = 0, 0, 0
            for word1, word2 in zip(sorted(no_match_1), sorted(no_match_2)):
                if word1[0:2] == word2[0:2]:
                    match_count += 1
                    uncertainties += len(word1) == 1 or len(word2) == 1
                else:
                    mismatched += 1
                    break

            if mismatched > 0:
                return False, 0.0
            if match_count >= 2:
                return True, 0.9 if uncertainties <= 1 else 0.8
            return False, 0.5 if uncertainties <= 1 else 0.4

        except Exception as err:
            print(f"Error in sc013_initials_check: {err}")
            return False, 0.0

    @staticmethod
    def sc015_word_missing(input_name, response_name):
        """
        Used for cases where 3 word string and 2 word string for match
           e.g.  "Archana Bholaram Gupta"  and "Archana Gupta"
        """
        try:
            is_matched = False
            score_output = 0
            name1_list = input_name.split()
            name2_list = response_name.split()
            if not ((len(name1_list) == 3 and len(name2_list) == 2) or (len(name1_list) == 2 and len(name2_list) == 3)):
                return is_matched, score_output
            if any(len(item) == 1 for item in (name1_list + name2_list)):
                return is_matched, score_output
            no_match_1 = list(set(name1_list) - set(name2_list))
            no_match_2 = list(set(name2_list) - set(name1_list))
            if (len(no_match_1) == 1) and not len(no_match_2) or (len(no_match_2) == 1 and not len(no_match_1)):
                score_output = 0.8
                is_matched = True
            return is_matched, score_output
        except Exception as err:
            print(f"Exception occurs while calculating the score. Error: {err}")
            return None

    @staticmethod
    def sc016_initials_vs_full_name(string1: str, string2: str):
        """
        Match when full names in one string correspond to initials in the other.
        Returns 0.8 only when every initial-to-full match is distinct and aligned.
        Evaluates both sorted and original token order, returning a match if either passes.
        """

        def tokenize(name):
            return re.findall(r"\b\w+\b", name)

        if not (any(len(word) == 1 for word in tokenize(string1)) or any(len(word) == 1 for word in tokenize(string2))):
            return False, 0.0

        def has_single_prefix_difference(token1, token2):
            no_match_1 = list(set(token1) - set(token2))
            no_match_2 = list(set(token2) - set(token1))
            if (
                len(no_match_1) == 1
                and len(no_match_2) == 1
                and (no_match_1[0].startswith(no_match_2[0]) or no_match_2[0].startswith(no_match_1[0]))
            ):
                return True

            return False

        def check_match(tokens1, tokens2):
            if len(tokens1) != len(tokens2):
                return False

            used_initials = set()
            for word1, word2 in zip(tokens1, tokens2):
                if word1 == word2:
                    continue
                elif any(item in soundex(word1) for item in soundex(word2) if len(item) > 1):
                    continue
                elif len(word1) == 1 and word2.startswith(word1):
                    if word1 in used_initials:
                        return False
                    used_initials.add(word1)
                elif len(word2) == 1 and word1.startswith(word2):
                    if word2 in used_initials:
                        return False
                    used_initials.add(word2)
                else:
                    return False

            return True

        tokens_orig_1 = tokenize(string1)
        tokens_orig_2 = tokenize(string2)

        tokens_sorted_1 = sorted(tokens_orig_1)
        tokens_sorted_2 = sorted(tokens_orig_2)

        is_all_initials_1 = all(len(token) == 1 for token in tokens_sorted_1)
        is_all_initials_2 = all(len(token) == 1 for token in tokens_sorted_2)
        if is_all_initials_1 or is_all_initials_2:
            return False, 0.0

        initials1 = [i for i in tokens_orig_1 if len(i) == 1]
        initials2 = [i for i in tokens_orig_2 if len(i) == 1]
        if len(initials1) == 1 and len(initials2) == 1:
            return False, 0.0

        if abs(len(initials1) - len(initials2)) >= 2:
            return False, 0.0

        if len(tokens_orig_1) == 1 or len(tokens_orig_2) == 1:
            return False, 0.0

        if len(tokens_orig_1) != len(tokens_orig_2):
            return False, 0.0

        if has_single_prefix_difference(tokens_orig_1, tokens_orig_2):
            return True, 0.8

        if check_match(tokens_orig_1, tokens_orig_2) or check_match(tokens_sorted_1, tokens_sorted_2):
            return True, 0.8
        return False, 0.0

    @staticmethod
    def sc014_soundex_matched(input_name: str, response_name: str):
        """
        Michael RAMKUMAR - Micheal Ramkumar -> 0.8
        """
        try:
            is_matched = False
            score_output = 0.0

            name1_list = input_name.split()
            name2_list = response_name.split()

            if len(name1_list) != len(name2_list):
                return is_matched, score_output

            no_match_1 = list(set(name1_list) - set(name2_list))
            no_match_2 = list(set(name2_list) - set(name1_list))

            if not no_match_1 and not no_match_2:
                return is_matched, score_output
            if len(no_match_1) != len(no_match_2):
                return is_matched, score_output

            joined_name1 = "".join(sorted(no_match_1))
            joined_name2 = "".join(sorted(no_match_2))
            if joined_name1 not in joined_name2 and joined_name2 not in joined_name1:
                if soundex(joined_name1) == soundex(joined_name2) and (
                    (joined_name1[1] in "aeiouhyw") == (joined_name2[1] in "aeiouhyw")
                ):
                    is_matched = True
                    score_output = 0.8
            return is_matched, score_output
        except Exception as err:
            print(f"Exception in SC014_soundex_matched for {input_name}, {response_name}: {err}")
            return False, 0.0

    def re001_soundex_unequal_names(self, input_name, response_name, score):
        is_matched = True

        name1_list = input_name.split()
        name2_list = response_name.split()

        if len(name2_list) != len(name1_list):
            return is_matched, score

        no_match_1 = [word for word in name1_list if word not in name2_list]
        no_match_2 = [word for word in name2_list if word not in name1_list]

        full_list1 = no_match_2 + no_match_1
        full_list2 = [x for x in full_list1 if len(x)]

        if len(sorted(full_list2)) == 2 and full_list2[1].startswith(full_list2[0]):
            return is_matched, score

        if not len(full_list2) or full_list2 != full_list1:
            return is_matched, score

        if set(no_match_1) == set(name1_list) or len(no_match_2) != len(no_match_1):
            return is_matched, score

        if no_match_1[0][0] != no_match_2[0][0]:
            is_matched = False
            score -= 0.2
            return is_matched, score

        try:
            joined_name1 = "".join(no_match_1)
            joined_name2 = "".join(no_match_2)

            if soundex(joined_name1) != soundex(joined_name2):
                score -= 0.1
                return False, score
            elif not NameMatchHelper.metaphone(input_name, response_name)[1]:
                score -= 0.1
        except Exception:
            pass

        if self.check_only_vowel(no_match_1[0], no_match_2[0]):
            return is_matched, score

        is_matched = False

        return is_matched, score

    def re002_initials_check(self, input_name, response_name, score):
        is_matched = True

        name1_list = input_name.split()
        name2_list = response_name.split()
        no_match_1 = [word for word in name1_list if word not in name2_list]
        no_match_2 = [word for word in name2_list if word not in name1_list]

        if not no_match_1 and not no_match_2:
            return is_matched, score

        if set(name1_list) == set(no_match_1) or set(name2_list) == set(no_match_2):
            return is_matched, score

        matched_count = abs(len(name1_list) - len(name2_list))
        if (no_match_1 and not no_match_2) or (no_match_2 and not no_match_1):
            score = 0.7 if matched_count >= 2 else 0.8
            return is_matched, score

        match_count = sum(1 for ele in no_match_1 for word in no_match_2 if ele[0] == word[0])
        if match_count > 0:
            return is_matched, score
        return is_matched, 0.7

    def re002_initials_check_v3(self, input_name, response_name, score):
        is_matched = True
        name1_list = input_name.split()
        name2_list = response_name.split()
        no_match_1 = [word for word in name1_list if word not in name2_list]
        no_match_2 = [word for word in name2_list if word not in name1_list]

        if not no_match_1 and not no_match_2:
            return is_matched, score
        if set(name1_list) == set(no_match_1) or set(name2_list) == set(no_match_2):
            return is_matched, score

        if len(name1_list) >= 3 or len(name2_list) >= 3:
            joined_name1, joined_name2 = "".join(name1_list), "".join(name2_list)
            if soundex(joined_name1) == soundex(joined_name2):
                if self.check_only_vowel("".join(no_match_1), "".join(no_match_2)):
                    return is_matched, score
                return is_matched, score - 0.1
            return False, score - 0.1

        matched_count = abs(len(name1_list) - len(no_match_1))
        if (no_match_1 and not no_match_2) or (no_match_2 and not no_match_1):
            score = 0.7 if matched_count >= 2 else 0.8
            return is_matched, score

        match_count = sum(1 for ele in no_match_1 for word in no_match_2 if ele[0] == word[0])
        if match_count > 0:
            return is_matched, score

        return is_matched, 0.7

    @staticmethod
    def re008_dec_unequal_names(input_name, response_name, score):
        is_matched = True
        if score > 0.7:
            if not input_name.startswith(response_name) or not response_name.startswith(input_name):
                score -= 0.1
        return is_matched, score

    @staticmethod
    def re003_two_words_vs_one(input_name: str, response_name: str, score: float):
        """
        Compares two names with multiple words, and adjusts the score based on phonetic similarity
        using the soundex algorithm. If names are phonetically different, a penalty is applied.

        :param input_name: The first name to compare.
        :param response_name: The second name to compare.
        :param score: The current score to adjust based on the comparison.
        :returns: Tuple indicating if names matched and the updated score.
        """
        name1_list = input_name.split()
        name2_list = response_name.split()
        if len(name1_list) == len(name2_list):
            return True, score
        full_name_parts = name1_list + name2_list
        filtered_name_parts = [word for word in full_name_parts if len(word) > 1]

        if not filtered_name_parts or filtered_name_parts != full_name_parts:
            return True, score

        joined_input_name = "".join(name1_list)
        joined_response_name = "".join(name2_list)
        try:

            if not (joined_input_name in joined_response_name or joined_response_name in joined_input_name) and soundex(
                joined_input_name
            ) != soundex(joined_response_name):
                score -= 0.1
                return False, score
        except Exception:
            print(f"soundex Exception | name1: {input_name} | name2: {response_name}")

        return True, score

    @staticmethod
    def re005_single_name_soundex(input_name: str, response_name: str, score: float):
        """
        Compare two names using the soundex algorithm and adjust the score.

        :param input_name: The first name to compare.
        :param response_name: The second name to compare.
        :param score: The current score to adjust if names do not match phonetically.
        :returns: Tuple indicating if names matched and the updated score.
        :rtype: tuple(bool, float)
        """
        is_matched = True

        name1_list = input_name.split()
        name2_list = response_name.split()

        filtered_name1 = [word for word in name1_list if len(word) > 1]
        filtered_name2 = [word for word in name2_list if len(word) > 1]

        if len(filtered_name1) != 1 or len(filtered_name2) != 1:
            return is_matched, score

        input_word = filtered_name1[0]
        response_word = filtered_name2[0]

        try:
            if soundex(input_word) != soundex(response_word):
                is_matched = False
                score -= 0.1
        except Exception:
            print(f"soundex Exception | name1: {input_name} | name2: {response_name}")

        return is_matched, score

    @staticmethod
    def re006_name_gender_check(input_name: str, response_name: str, score: float):
        """
        Checks name match with gender-based suffix handling.
        Examples:
        - 'Praveen' and 'Praveena' -> -0.3 score penalty.
        - 'Selva Kumar' and 'Selva Kumari' -> -0.3 score penalty.
        - 'Rama Krishna' and 'Rama krishnaa' -> No penalty (last-before letter is 'a').
        """
        is_matched = True

        name1_list = input_name.split()
        name2_list = response_name.split()

        no_match_1 = set(name1_list) - set(name2_list)
        no_match_2 = set(name2_list) - set(name1_list)

        for word1 in no_match_1:
            for word2 in no_match_2:
                if (
                    word1 == word2[:-1]
                    and word2[-1] in {"a", "i"}
                    and (len(word2) > 1 and word2[-2] != "a")
                    or (word2 == word1[:-1] and word1[-1] in {"a", "i"} and (len(word1) > 1 and word1[-2] != "a"))
                ):
                    is_matched = False
                    score -= 0.3

        return is_matched, score

    @staticmethod
    def re010_is_exact_match(input_name: str, response_name: str, score: float):
        # Early exit if the score is not 1.0
        if not math.isclose(score, 1.0, abs_tol=1e-9):
            return True, score

        name1_list = input_name.split(" ")
        name2_list = response_name.split(" ")
        if "".join(name1_list) != "".join(name2_list):
            return True, 0.9

        if len(name1_list) == len(name2_list):

            if all(n1[0] == n2[0] for n1, n2 in zip(name1_list, name2_list)):
                return True, score

        no_match_1 = set(name1_list) - set(name2_list)
        no_match_2 = set(name2_list) - set(name1_list)

        if not no_match_1 and not no_match_2:
            return True, score

        score -= 0.1
        return True, score
