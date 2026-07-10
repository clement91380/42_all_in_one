"""Exam database — exercises from 42 exam ranks 02-06."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ExamExercise:
    rank: int
    name: str
    subject: str
    difficulty: int  # 1-5
    language: str  # "c", "cpp", "shell"
    topics: list[str] = field(default_factory=list)
    example_input: str = ""
    example_output: str = ""
    hints: list[str] = field(default_factory=list)


EXAM_DATABASE: list[ExamExercise] = [
    # === RANK 02 ===
    ExamExercise(
        rank=2, name="ft_strcpy", subject=(
            "Reproduce the behavior of the function strcpy.\n"
            "Prototype: char *ft_strcpy(char *s1, char *s2);"
        ),
        difficulty=1, language="c", topics=["strings", "pointers"],
        hints=["Copy characters one by one including '\\0'"],
    ),
    ExamExercise(
        rank=2, name="ft_strlen", subject=(
            "Write a function that returns the length of a string.\n"
            "Prototype: int ft_strlen(char *str);"
        ),
        difficulty=1, language="c", topics=["strings", "loops"],
        hints=["Iterate until '\\0'"],
    ),
    ExamExercise(
        rank=2, name="ft_swap", subject=(
            "Write a function that swaps the value of two integers.\n"
            "Prototype: void ft_swap(int *a, int *b);"
        ),
        difficulty=1, language="c", topics=["pointers"],
        hints=["Use a temporary variable"],
    ),
    ExamExercise(
        rank=2, name="ft_putstr", subject=(
            "Write a function that displays a string on stdout.\n"
            "Prototype: void ft_putstr(char *str);"
        ),
        difficulty=1, language="c", topics=["write", "strings"],
        hints=["Use write(1, &c, 1) in a loop"],
    ),
    ExamExercise(
        rank=2, name="first_word", subject=(
            "Write a program that takes a string and displays its first word,\n"
            "followed by a newline. A word is a section of string delimited by\n"
            "spaces/tabs or by the start/end of the string."
        ),
        difficulty=1, language="c", topics=["strings", "parsing"],
    ),
    ExamExercise(
        rank=2, name="fizzbuzz", subject=(
            "Write a program that prints numbers from 1 to 100.\n"
            "For multiples of 3: 'fizz', of 5: 'buzz', of both: 'fizzbuzz'."
        ),
        difficulty=1, language="c", topics=["loops", "conditions"],
    ),
    ExamExercise(
        rank=2, name="repeat_alpha", subject=(
            "Write a program that takes a string and displays each character\n"
            "repeated N times where N is its alphabetical position.\n"
            "'a' appears 1 time, 'b' 2 times, etc."
        ),
        difficulty=2, language="c", topics=["strings", "ascii"],
    ),
    ExamExercise(
        rank=2, name="rev_print", subject=(
            "Write a program that takes a string and displays it in reverse.\n"
        ),
        difficulty=1, language="c", topics=["strings"],
    ),
    ExamExercise(
        rank=2, name="rotone", subject=(
            "Write a program that displays its first argument with each letter\n"
            "shifted by one position in the alphabet ('z' becomes 'a')."
        ),
        difficulty=1, language="c", topics=["strings", "ascii", "cipher"],
    ),
    ExamExercise(
        rank=2, name="search_and_replace", subject=(
            "Write a program that takes 3 arguments: a string, a char to find,\n"
            "and a char to replace it with. Display the modified string."
        ),
        difficulty=1, language="c", topics=["strings", "parsing"],
    ),
    ExamExercise(
        rank=2, name="ulstr", subject=(
            "Write a program that takes a string and swaps its letter cases.\n"
            "Uppercase becomes lowercase and vice versa."
        ),
        difficulty=1, language="c", topics=["strings", "ascii"],
    ),
    ExamExercise(
        rank=2, name="camel_to_snake", subject=(
            "Write a program that converts camelCase to snake_case.\n"
            "Example: 'helloWorld' -> 'hello_world'"
        ),
        difficulty=2, language="c", topics=["strings", "conversion"],
    ),
    ExamExercise(
        rank=2, name="inter", subject=(
            "Write a program that takes 2 strings and displays characters\n"
            "that appear in both strings without duplicates, in order of first string."
        ),
        difficulty=2, language="c", topics=["strings", "sets"],
    ),
    ExamExercise(
        rank=2, name="last_word", subject=(
            "Write a program that takes a string and displays its last word.\n"
            "A word is separated by spaces/tabs."
        ),
        difficulty=1, language="c", topics=["strings", "parsing"],
    ),
    ExamExercise(
        rank=2, name="max", subject=(
            "Write a function that returns the largest int in an array.\n"
            "Prototype: int max(int *tab, unsigned int len);"
        ),
        difficulty=1, language="c", topics=["arrays", "loops"],
    ),
    ExamExercise(
        rank=2, name="print_bits", subject=(
            "Write a function that prints the binary representation of a byte.\n"
            "Prototype: void print_bits(unsigned char octet);"
        ),
        difficulty=2, language="c", topics=["bitwise", "binary"],
    ),
    ExamExercise(
        rank=2, name="reverse_bits", subject=(
            "Write a function that reverses the bits of a byte.\n"
            "Prototype: unsigned char reverse_bits(unsigned char octet);"
        ),
        difficulty=2, language="c", topics=["bitwise"],
    ),
    ExamExercise(
        rank=2, name="wdmatch", subject=(
            "Write a program that takes 2 strings, prints the first if all its\n"
            "characters can be found in the second (in order)."
        ),
        difficulty=2, language="c", topics=["strings", "matching"],
    ),

    # === RANK 03 ===
    ExamExercise(
        rank=3, name="ft_atoi_base", subject=(
            "Write a function that converts a string base representation to int.\n"
            "Prototype: int ft_atoi_base(const char *str, const char *base);"
        ),
        difficulty=3, language="c", topics=["conversion", "bases"],
    ),
    ExamExercise(
        rank=3, name="ft_list_size", subject=(
            "Write a function that returns the number of elements in a linked list.\n"
            "Prototype: int ft_list_size(t_list *begin_list);"
        ),
        difficulty=2, language="c", topics=["linked_lists"],
    ),
    ExamExercise(
        rank=3, name="ft_range", subject=(
            "Write a function that returns an int array from min to max.\n"
            "Prototype: int *ft_range(int start, int end);"
        ),
        difficulty=2, language="c", topics=["malloc", "arrays"],
    ),
    ExamExercise(
        rank=3, name="ft_rrange", subject=(
            "Write a function that returns an int array from max to min.\n"
            "Prototype: int *ft_rrange(int start, int end);"
        ),
        difficulty=2, language="c", topics=["malloc", "arrays"],
    ),
    ExamExercise(
        rank=3, name="add_prime_sum", subject=(
            "Write a program that takes a positive int and displays the sum\n"
            "of all prime numbers inferior or equal to it."
        ),
        difficulty=2, language="c", topics=["math", "primes"],
    ),
    ExamExercise(
        rank=3, name="epur_str", subject=(
            "Write a program that takes a string and displays it with exactly\n"
            "one space between words, no leading/trailing spaces."
        ),
        difficulty=2, language="c", topics=["strings", "parsing"],
    ),
    ExamExercise(
        rank=3, name="expand_str", subject=(
            "Write a program that takes a string and displays it with 3 spaces\n"
            "between each word instead of one."
        ),
        difficulty=2, language="c", topics=["strings", "formatting"],
    ),
    ExamExercise(
        rank=3, name="ft_split", subject=(
            "Write a function that splits a string into words.\n"
            "Prototype: char **ft_split(char *str);"
        ),
        difficulty=3, language="c", topics=["strings", "malloc", "arrays"],
    ),
    ExamExercise(
        rank=3, name="hidenp", subject=(
            "Write a program that takes 2 strings. Display 1 if s1 is hidden\n"
            "in s2 (characters appear in order), 0 otherwise."
        ),
        difficulty=2, language="c", topics=["strings", "subsequence"],
    ),
    ExamExercise(
        rank=3, name="lcm", subject=(
            "Write a function that returns the LCM of two unsigned ints.\n"
            "Prototype: unsigned int lcm(unsigned int a, unsigned int b);"
        ),
        difficulty=2, language="c", topics=["math"],
    ),
    ExamExercise(
        rank=3, name="paramsum", subject=(
            "Write a program that displays the number of arguments passed to it."
        ),
        difficulty=1, language="c", topics=["argc"],
    ),
    ExamExercise(
        rank=3, name="pgcd", subject=(
            "Write a program that takes 2 strings representing ints and\n"
            "displays their greatest common divisor."
        ),
        difficulty=2, language="c", topics=["math", "gcd"],
    ),
    ExamExercise(
        rank=3, name="tab_mult", subject=(
            "Write a program that displays the multiplication table of\n"
            "a given number (passed as parameter)."
        ),
        difficulty=1, language="c", topics=["loops", "arithmetic"],
    ),

    # === RANK 04 ===
    ExamExercise(
        rank=4, name="flood_fill", subject=(
            "Write a function that fills a zone on a char** map.\n"
            "Prototype: void flood_fill(char **tab, t_point size, t_point begin);"
        ),
        difficulty=3, language="c", topics=["recursion", "2d_arrays", "algorithms"],
    ),
    ExamExercise(
        rank=4, name="fprime", subject=(
            "Write a program that displays the prime factorization of a number.\n"
            "Example: 225 -> '3*3*5*5'"
        ),
        difficulty=2, language="c", topics=["math", "primes", "factorization"],
    ),
    ExamExercise(
        rank=4, name="ft_itoa", subject=(
            "Write a function that converts an int to a null-terminated string.\n"
            "Prototype: char *ft_itoa(int nbr);"
        ),
        difficulty=2, language="c", topics=["conversion", "malloc"],
    ),
    ExamExercise(
        rank=4, name="ft_list_foreach", subject=(
            "Write a function that applies a function to each element of a list.\n"
            "Prototype: void ft_list_foreach(t_list *begin_list, void (*f)(void *));"
        ),
        difficulty=2, language="c", topics=["linked_lists", "function_pointers"],
    ),
    ExamExercise(
        rank=4, name="ft_list_remove_if", subject=(
            "Write a function that removes elements from list that match a reference.\n"
            "Prototype: void ft_list_remove_if(t_list **begin, void *ref, int (*cmp)());"
        ),
        difficulty=3, language="c", topics=["linked_lists", "function_pointers", "free"],
    ),
    ExamExercise(
        rank=4, name="rev_wstr", subject=(
            "Write a program that takes a string and displays its words in reverse.\n"
            "Example: 'Hello World' -> 'World Hello'"
        ),
        difficulty=2, language="c", topics=["strings", "parsing"],
    ),
    ExamExercise(
        rank=4, name="rostring", subject=(
            "Write a program that rotates the first word to the end of the string.\n"
            "Example: 'abc def ghi' -> 'def ghi abc'"
        ),
        difficulty=2, language="c", topics=["strings", "rotation"],
    ),
    ExamExercise(
        rank=4, name="sort_int_tab", subject=(
            "Write a function that sorts an integer array.\n"
            "Prototype: void sort_int_tab(int *tab, unsigned int size);"
        ),
        difficulty=2, language="c", topics=["sorting", "arrays"],
    ),
    ExamExercise(
        rank=4, name="sort_list", subject=(
            "Write a function that sorts a linked list using a comparison function.\n"
            "Prototype: t_list *sort_list(t_list *lst, int (*cmp)(int, int));"
        ),
        difficulty=3, language="c", topics=["linked_lists", "sorting"],
    ),

    # === RANK 05 ===
    ExamExercise(
        rank=5, name="ft_printf", subject=(
            "Write a simplified printf that handles: %%s, %%d, %%x.\n"
            "Prototype: int ft_printf(const char *, ...);"
        ),
        difficulty=4, language="c", topics=["variadic", "formatting", "write"],
    ),
    ExamExercise(
        rank=5, name="get_next_line", subject=(
            "Write a function that reads a line from a file descriptor.\n"
            "Prototype: char *get_next_line(int fd);\n"
            "Returns the line read, or NULL if nothing else to read."
        ),
        difficulty=4, language="c", topics=["fd", "malloc", "static", "read"],
    ),

    # === RANK 06 ===
    ExamExercise(
        rank=6, name="mini_serv", subject=(
            "Write a simple IRC-like server using select().\n"
            "Clients can connect, send messages that are broadcast to all others."
        ),
        difficulty=5, language="c", topics=["sockets", "select", "networking"],
    ),
]


def get_exercises_by_rank(rank: int) -> list[ExamExercise]:
    return [e for e in EXAM_DATABASE if e.rank == rank]


def get_exercise_by_name(name: str) -> ExamExercise | None:
    for e in EXAM_DATABASE:
        if e.name == name:
            return e
    return None


def get_all_topics() -> list[str]:
    topics = set()
    for e in EXAM_DATABASE:
        topics.update(e.topics)
    return sorted(topics)


def search_exercises(query: str) -> list[ExamExercise]:
    query = query.lower()
    results = []
    for e in EXAM_DATABASE:
        if (query in e.name.lower() or
            query in e.subject.lower() or
            any(query in t for t in e.topics)):
            results.append(e)
    return results
