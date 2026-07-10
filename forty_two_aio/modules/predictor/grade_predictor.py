"""Grade predictor — estimates project score based on verifiable criteria."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GradeCriteria:
    name: str
    weight: float  # 0.0 - 1.0
    passed: bool = False
    details: str = ""


@dataclass
class GradePrediction:
    project_name: str
    estimated_score: int  # 0-125
    criteria: list[GradeCriteria] = field(default_factory=list)
    confidence: str = "medium"  # low, medium, high
    notes: list[str] = field(default_factory=list)

    @property
    def would_pass(self) -> bool:
        return self.estimated_score >= 80


# Criteria weights per project type
PROJECT_CRITERIA = {
    "libft": [
        ("compilation", 0.15, "Compiles with -Wall -Wextra -Werror"),
        ("norminette", 0.10, "No norminette errors"),
        ("no_forbidden_func", 0.10, "No forbidden functions used"),
        ("mandatory_functions", 0.50, "All mandatory functions present and correct"),
        ("bonus_functions", 0.15, "Bonus functions (lst_*)"),
    ],
    "ft_printf": [
        ("compilation", 0.15, "Compiles with -Wall -Wextra -Werror"),
        ("norminette", 0.10, "No norminette errors"),
        ("conversions_basic", 0.30, "Handles %c %s %p %d %i %u %x %X %%"),
        ("edge_cases", 0.20, "NULL string, INT_MIN, 0 pointer"),
        ("return_value", 0.15, "Correct return value (chars printed)"),
        ("no_leaks", 0.10, "No memory leaks"),
    ],
    "get_next_line": [
        ("compilation", 0.15, "Compiles with -Wall -Wextra -Werror"),
        ("norminette", 0.10, "No norminette errors"),
        ("basic_read", 0.25, "Reads lines correctly from fd"),
        ("multiple_fd", 0.20, "Handles multiple fd (bonus)"),
        ("buffer_size", 0.15, "Works with different BUFFER_SIZE"),
        ("no_leaks", 0.15, "No memory leaks"),
    ],
    "push_swap": [
        ("compilation", 0.10, "Compiles with -Wall -Wextra -Werror"),
        ("norminette", 0.10, "No norminette errors"),
        ("sort_3", 0.10, "Sorts 3 numbers"),
        ("sort_5", 0.15, "Sorts 5 in <= 12 moves"),
        ("sort_100", 0.25, "Sorts 100 in < 700 moves"),
        ("sort_500", 0.20, "Sorts 500 in < 5500 moves"),
        ("error_handling", 0.10, "Handles errors (duplicates, non-int, overflow)"),
    ],
    "pipex": [
        ("compilation", 0.15, "Compiles with -Wall -Wextra -Werror"),
        ("norminette", 0.10, "No norminette errors"),
        ("basic_pipe", 0.30, "Basic piping works (cmd1 | cmd2)"),
        ("heredoc", 0.15, "Here_doc bonus"),
        ("multiple_pipes", 0.15, "Multiple pipes"),
        ("error_handling", 0.15, "Command not found, permission denied"),
    ],
    "so_long": [
        ("compilation", 0.10, "Compiles with -Wall -Wextra -Werror"),
        ("norminette", 0.10, "No norminette errors"),
        ("map_parsing", 0.20, "Valid map parsing (walls, player, exit, collectibles)"),
        ("display", 0.20, "Game displays correctly"),
        ("movement", 0.20, "Player moves with WASD/arrows"),
        ("win_condition", 0.10, "Game ends when all collected + exit reached"),
        ("move_counter", 0.10, "Move count displayed"),
    ],
    "philosophers": [
        ("compilation", 0.10, "Compiles with -Wall -Wextra -Werror"),
        ("norminette", 0.10, "No norminette errors"),
        ("no_deadlock", 0.20, "No deadlock"),
        ("death_timing", 0.20, "Philosopher dies at correct time (±10ms)"),
        ("data_race", 0.15, "No data races (helgrind/tsan clean)"),
        ("eat_count", 0.15, "Stops when all have eaten N times"),
        ("one_philo", 0.10, "Handles 1 philosopher correctly"),
    ],
    "minishell": [
        ("compilation", 0.10, "Compiles with -Wall -Wextra -Werror"),
        ("norminette", 0.05, "No norminette errors"),
        ("builtins", 0.20, "echo, cd, pwd, export, unset, env, exit"),
        ("pipes", 0.15, "Pipes work correctly"),
        ("redirections", 0.15, ">, >>, <, << work"),
        ("env_variables", 0.10, "$ expansion works"),
        ("quotes", 0.10, "Single and double quotes"),
        ("signals", 0.10, "Ctrl+C, Ctrl+D, Ctrl+\\"),
        ("no_leaks", 0.05, "Minimal memory leaks"),
    ],
    "generic": [
        ("compilation", 0.20, "Compiles with -Wall -Wextra -Werror"),
        ("norminette", 0.15, "No norminette errors"),
        ("functionality", 0.40, "Core functionality works"),
        ("error_handling", 0.15, "Proper error handling"),
        ("no_leaks", 0.10, "No memory leaks"),
    ],
}


def predict_grade(
    project_name: str,
    checks: dict[str, bool],
) -> GradePrediction:
    """Predict grade based on which criteria pass.

    Args:
        project_name: Name of the 42 project (e.g., "libft", "ft_printf")
        checks: Dict mapping criteria names to pass/fail booleans
    """
    criteria_defs = PROJECT_CRITERIA.get(
        project_name.lower(), PROJECT_CRITERIA["generic"]
    )

    criteria = []
    total_weight = 0.0
    passed_weight = 0.0

    for name, weight, description in criteria_defs:
        passed = checks.get(name, False)
        criteria.append(GradeCriteria(
            name=name,
            weight=weight,
            passed=passed,
            details=description,
        ))
        total_weight += weight
        if passed:
            passed_weight += weight

    base_score = int((passed_weight / total_weight) * 100) if total_weight > 0 else 0

    bonus_score = 0
    if base_score >= 100:
        bonus_score = min(25, sum(5 for k, v in checks.items() if k.startswith("bonus_") and v))

    estimated = min(125, base_score + bonus_score)

    confidence = "high" if len(checks) >= len(criteria_defs) * 0.8 else "medium"
    if len(checks) < len(criteria_defs) * 0.5:
        confidence = "low"

    prediction = GradePrediction(
        project_name=project_name,
        estimated_score=estimated,
        criteria=criteria,
        confidence=confidence,
    )

    if not checks.get("compilation"):
        prediction.notes.append("Project won't compile — likely 0 at evaluation")
    if not checks.get("norminette"):
        prediction.notes.append("Norm errors may cause -42 at peer evaluation")

    return prediction


def detect_project_from_files(files: list[str]) -> str:
    """Detect which 42 project this is based on file names."""
    file_set = {f.lower() for f in files}
    names = " ".join(files).lower()

    if "libft.h" in file_set or "ft_isalpha.c" in file_set:
        return "libft"
    if "ft_printf.c" in file_set or "ft_printf.h" in file_set:
        return "ft_printf"
    if "get_next_line.c" in file_set or "get_next_line.h" in file_set:
        return "get_next_line"
    if "push_swap.h" in file_set or "push_swap.c" in file_set:
        return "push_swap"
    if "pipex.h" in file_set or "pipex.c" in file_set:
        return "pipex"
    if "so_long.h" in file_set:
        return "so_long"
    if "philo" in names and ("thread" in names or "mutex" in names):
        return "philosophers"
    if "minishell.h" in file_set:
        return "minishell"

    return "generic"
