from janito.agent.runtime_config import runtime_config


def handle_prompt(console, shell_state=None, **kwargs):
    profile_manager = kwargs.get("profile_manager")
    if not profile_manager and shell_state and hasattr(shell_state, "profile_manager"):
        profile_manager = shell_state.profile_manager
    prompt = None
    if profile_manager:
        prompt = profile_manager.system_prompt_template
        if not prompt:
            profile_manager.refresh_prompt()
            prompt = profile_manager.system_prompt_template
    if not prompt:
        console.print(
            "[bold red]System prompt is not initialized. Please check your profile configuration.[/bold red]"
        )
    else:
        console.print(f"[bold magenta]System Prompt:[/bold magenta]\n{prompt}")


handle_prompt.help_text = "Show the system prompt"


def handle_role(console, args=None, shell_state=None, **kwargs):
    profile_manager = (
        shell_state.profile_manager
        if shell_state and hasattr(shell_state, "profile_manager")
        else kwargs.get("profile_manager")
    )
    if not args:
        console.print("[bold red]Usage: /role <new role description>[/bold red]")
        return
    new_role = " ".join(args)
    if profile_manager:
        profile_manager.set_role(new_role)
    # Update system message in conversation
    found = False
    for msg in shell_state.conversation_history.get_messages():
        if msg.get("role") == "system":
            msg["content"] = (
                profile_manager.system_prompt_template if profile_manager else new_role
            )
            found = True
            break
    if not found:
        if shell_state and hasattr(shell_state, "conversation_history"):
            shell_state.conversation_history.set_system_message(new_role)
    # Also store the raw role string
    if profile_manager:
        setattr(profile_manager, "role_name", new_role)
    runtime_config.set("role", new_role)
    console.print(f"[bold green]System role updated to:[/bold green] {new_role}")


handle_role.help_text = "Change the system role"


def handle_profile(console, *args, **kwargs):
    """/profile - Show the current and available Agent Profile (only 'base' is supported)"""
    console.print("[bold green]Current profile:[/bold green] base")
    console.print("[bold yellow]Available profiles:[/bold yellow]\n- base")
