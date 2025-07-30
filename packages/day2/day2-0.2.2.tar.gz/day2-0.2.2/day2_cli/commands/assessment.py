"""Assessment commands for the MontyCloud DAY2 CLI."""

import json
from typing import Any, Optional, Tuple

import click
from rich.console import Console

from day2 import Session
from day2.exceptions import Day2Error
from day2.models.assessment import AnswerQuestionInput, CreateAssessmentInput
from day2_cli.utils.formatters import format_error
from day2_cli.utils.output_formatter import (
    format_item_output,
    format_list_output,
    format_simple_output,
)

console = Console()


def get_tenant_id(session: Session, tenant_id: Optional[str]) -> Optional[str]:
    """Get the tenant ID from the provided value or session default.

    Args:
        session: The session object
        tenant_id: The provided tenant ID or None

    Returns:
        The tenant ID to use or None if not available
    """
    if tenant_id:
        return tenant_id

    tenant_id = session.tenant_id
    if not tenant_id:
        console.print(
            "[red]Error: No tenant ID provided and no default tenant configured.[/red]"
        )
        console.print(
            "[yellow]Tip: Configure a default tenant with 'day2 config set tenant-id YOUR_TENANT_ID'[/yellow]"
        )
        return None

    return tenant_id


@click.group()
def assessment() -> None:
    """Assessment commands."""


@assessment.command("list")
@click.option("--tenant-id", help="ID of the tenant to list assessments for")
@click.option("--status", help="Filter by assessment status (PENDING or COMPLETED)")
@click.option("--keyword", help="Filter by keyword")
@click.option("--page-token", help="Page token for pagination")
@click.option("--page-size", type=int, default=10, help="Page size")
@click.option(
    "--output",
    type=click.Choice(["table", "json"], case_sensitive=False),
    help="Output format (table or json)",
)
def list_assessments(
    tenant_id: Optional[str],
    status: Optional[str],
    keyword: Optional[str],
    page_token: Optional[str],
    page_size: int,
    output: Optional[str] = None,
) -> None:
    """List assessments for a tenant.

    If --tenant-id is not provided, uses the default tenant configured with 'day2 config set tenant-id YOUR_TENANT_ID'.
    """
    try:
        # Get output format from context if set via global option
        ctx = click.get_current_context()
        ctx_output = ctx.obj.get("output_format") if ctx.obj else None
        output_format = output or ctx_output

        session = Session()

        # Get tenant ID from provided value or session default
        tenant_id = get_tenant_id(session, tenant_id)
        if not tenant_id:
            return

        # Call the client method with explicit parameters
        # Ensure status is not None when passing to the API
        status_value = status or "PENDING"  # Default to PENDING if not specified

        result = session.assessment.list_assessments(
            tenant_id=tenant_id,
            status=status_value,
            keyword=keyword,
            page_token=page_token,
            page_size=page_size,
        )

        if not result.assessments:
            format_simple_output("No assessments found.", format_override=output_format)
            return

        # Convert assessment objects to dictionaries for the formatter
        assessments_data = []
        for assessment_item in result.assessments:
            created_at = (
                assessment_item.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if assessment_item.created_at
                else "N/A"
            )
            assessments_data.append(
                {
                    "id": assessment_item.id,
                    "name": assessment_item.name,
                    "status": assessment_item.status,
                    "total_questions": assessment_item.total_questions,
                    "answered_questions": assessment_item.answered_questions,
                    "created_at": created_at,
                }
            )

        # Define column mapping for the formatter
        columns = {
            "id": "ID",
            "name": "Name",
            "status": "Status",
            "total_questions": "Total Questions",
            "answered_questions": "Answered Questions",
            "created_at": "Created At",
        }

        # Format and output the results
        format_list_output(
            items=assessments_data,
            title=f"Assessments for Tenant: {tenant_id}",
            columns=columns,
            format_override=output_format,
        )

        # Display pagination information
        if result.next_page_token:
            format_simple_output(
                f"More results available. Use --page-token={result.next_page_token} to get the next page.",
                format_override=output_format,
            )

    except Day2Error as e:
        console.print(format_error(e))


@assessment.command("get")
@click.option("--tenant-id", help="ID of the tenant that owns the assessment")
@click.argument("assessment-id")
@click.option(
    "--output",
    type=click.Choice(["table", "json"], case_sensitive=False),
    help="Output format (table or json)",
)
def get_assessment(
    tenant_id: Optional[str], assessment_id: str, output: Optional[str] = None
) -> None:
    """Get details of an assessment.

    If --tenant-id is not provided, uses the default tenant configured with 'auth configure'.

    ASSESSMENT-ID: ID of the assessment to get details for.
    """
    try:
        # Get output format from context if set via global option
        ctx = click.get_current_context()
        ctx_output = ctx.obj.get("output_format") if ctx.obj else None
        output_format = output or ctx_output

        session = Session()

        # Get tenant ID from provided value or session default
        tenant_id = get_tenant_id(session, tenant_id)
        if not tenant_id:
            return

        # Call the client method with explicit parameters
        result = session.assessment.get_assessment(tenant_id, assessment_id)

        # Format timestamps
        created_at = (
            result.created_at.strftime("%Y-%m-%d %H:%M:%S")
            if result.created_at
            else "N/A"
        )
        updated_at = (
            result.updated_at.strftime("%Y-%m-%d %H:%M:%S")
            if result.updated_at
            else "N/A"
        )
        last_run_at = (
            result.last_run_at.strftime("%Y-%m-%d %H:%M:%S")
            if result.last_run_at
            else "N/A"
        )

        # Convert assessment object to dictionary for the formatter
        assessment_data = {
            "ID": result.id,
            "Name": result.name,
            "Description": result.description or "N/A",
            "Status": result.status,
            "Assessment ARN": result.assessment_arn,
            "Owner": result.owner,
            "Diagram URL": result.diagram_url or "N/A",
            "Environment": result.environment or "N/A",
            "Improvement Status": result.improvement_status,
            "In Sync": result.in_sync,
            "Industry": result.industry or "N/A",
            "Industry Type": result.industry_type or "N/A",
            "Region": result.region_code or "N/A",
            "Scope": result.scope or "N/A",
            "Risk Counts": result.risk_counts,
            "Total Questions": result.total_questions,
            "Answered Questions": result.answered_questions,
            "Lenses": ", ".join(result.lenses) if result.lenses else "N/A",
            "Lens Alias": result.lens_alias,
            "Lens ARN": result.lens_arn,
            "Lens Version": result.lens_version,
            "Lens Name": result.lens_name,
            "Lens Status": result.lens_status,
            "AWS Updated At": result.aws_updated_at,
            "Created At": created_at,
            "Updated At": updated_at,
            "Last Run At": last_run_at,
            "Execution ID": result.execution_id or "N/A",
        }

        # Format and output the results
        format_item_output(
            item=assessment_data,
            title=f"Assessment Details: {result.name}",
            format_override=output_format,
        )

    except Day2Error as e:
        console.print(format_error(e))


@assessment.command("create")
@click.option("--tenant-id", help="ID of the tenant to create the assessment for")
@click.option("--name", required=True, help="Name of the assessment")
@click.option("--description", help="Description of the assessment")
@click.option("--review-owner", help="Email of the review owner")
@click.option(
    "--scope",
    help='Scope of the assessment as JSON string. Format: {"Project": {}, "Accounts": [{"AccountNumber": "123456789012", "Regions": ["us-east-1"]}]} or for project-based: {"Project": {"ProjectId": "project-123", "Applications": ["app1"]}, "Accounts": ["123456789012"]}',
)
@click.option("--lenses", help="Lenses to use for the assessment (comma-separated)")
@click.option(
    "--region-code", default="us-east-1", help="AWS region code (default: us-east-1)"
)
@click.option(
    "--environment", default="PRODUCTION", help="Environment (default: PRODUCTION)"
)
def create_assessment(
    tenant_id: Optional[str],
    name: str,
    description: Optional[str],
    review_owner: Optional[str],
    scope: Optional[str],
    lenses: Optional[str],
    region_code: str,
    environment: str,
) -> None:
    """Create a new assessment.

    If --tenant-id is not provided, uses the default tenant configured with 'auth configure'.
    """
    try:
        session = Session()

        # Get tenant ID from provided value or session default
        tenant_id = get_tenant_id(session, tenant_id)
        if not tenant_id:
            return

        # Parse the scope JSON string
        if not scope:
            console.print("[red]Error: Scope is required[/red]")
            return

        try:
            scope_data = json.loads(scope)
            if not isinstance(scope_data, dict):
                console.print(
                    "[red]Error: Scope must be a JSON object (dictionary), not a list or primitive value[/red]"
                )
                return
        except json.JSONDecodeError:
            console.print("[red]Error: Scope must be a valid JSON string[/red]")
            return

        # Parse lenses if provided
        lenses_list = []
        if lenses:
            lenses_list = [lens.strip() for lens in lenses.split(",")]

        # Set default values for optional parameters
        description_value = description or ""
        review_owner_value = review_owner or ""

        # Create a proper CreateAssessmentInput object
        assessment_input = CreateAssessmentInput(
            AssessmentName=name,
            Description=description_value,
            ReviewOwner=review_owner_value,
            Scope=scope_data,
            Lenses=lenses_list,
            RegionCode=region_code,
            Environment=environment,
        )

        result = session.assessment.create_assessment(
            tenant_id=tenant_id, data=assessment_input
        )

        console.print("[green]Assessment created successfully![/green]")
        console.print(f"Assessment ID: [cyan]{result.id}[/cyan]")
        console.print(f"Assessment Name: [green]{name}[/green]")

    except Day2Error as e:
        console.print(format_error(e))


@assessment.command("questions")
@click.option("--tenant-id", help="ID of the tenant that owns the assessment")
@click.argument("assessment-id")
@click.argument("pillar-id")
@click.option(
    "--output",
    type=click.Choice(["table", "json"], case_sensitive=False),
    help="Output format (table or json)",
)
def list_questions(
    tenant_id: Optional[str],
    assessment_id: str,
    pillar_id: str,
    output: Optional[str] = None,
) -> None:
    """List questions for a specific pillar in an assessment.

    If --tenant-id is not provided, uses the default tenant configured with 'auth configure'.

    ASSESSMENT-ID: ID of the assessment to list questions for.
    PILLAR-ID: ID of the pillar to list questions for (required).
    """
    try:
        # Get output format from context if set via global option
        ctx = click.get_current_context()
        ctx_output = ctx.obj.get("output_format") if ctx.obj else None
        output_format = output or ctx_output

        session = Session()

        # Get tenant ID from provided value or session default
        tenant_id = get_tenant_id(session, tenant_id)
        if not tenant_id:
            return

        # Call the client method with explicit parameters
        result = session.assessment.list_questions(
            tenant_id=tenant_id,
            assessment_id=assessment_id,
            pillar_id=pillar_id,
        )

        # Ensure we handle None values properly for the calculation
        total = result.total_questions or 0
        answered = result.answered_questions or 0
        remaining = total - answered

        # Display summary information
        summary_data = {
            "pillar_id": pillar_id,
            "total_questions": total,
            "answered_questions": answered,
            "remaining_questions": remaining,
        }

        if output_format == "json":
            # For JSON output, include the summary in the response
            questions_data: list[dict[str, Any]] = []
        else:
            # For table output, display the summary first
            format_simple_output(
                f"Pillar: {pillar_id}\nQuestions: {total} total, {answered} answered, {remaining} remaining",
                format_override=output_format,
            )

            # Create a table for the questions
            questions_data = []

        # Process each question
        for i, question in enumerate(result.questions, 1):
            # Determine status for display
            is_answered = question.is_answered or False
            status_text = "Answered" if is_answered else "Not Answered"
            risk = question.risk if question.risk else "N/A"

            # Add to questions data
            questions_data.append(
                {
                    "index": i,
                    "id": question.id,
                    "title": question.title,
                    "is_answered": is_answered,
                    "status": status_text,
                    "risk": risk,
                }
            )

        # Format and output the results
        if output_format == "json":
            # For JSON output, include both summary and questions
            output_data = {"summary": summary_data, "questions": questions_data}
            console.print(json.dumps(output_data, indent=2, default=str))
        else:
            # For table output, display the questions table
            columns = {
                "index": "#",
                "id": "Question ID",
                "title": "Title",
                "status": "Status",
                "risk": "Risk",
            }

            format_list_output(
                items=questions_data,
                title=f"Questions for Pillar: {pillar_id}",
                columns=columns,
                format_override=output_format,
            )

            # Add hint for more details
            format_simple_output(
                "To see details of a specific question, use the 'question get' command with the Question ID.",
                format_override=output_format,
            )

    except Day2Error as e:
        console.print(format_error(e))


@assessment.command("question")
@click.option("--tenant-id", help="ID of the tenant that owns the assessment")
@click.argument("assessment-id")
@click.argument("question-id")
@click.option(
    "--output",
    type=click.Choice(["table", "json"], case_sensitive=False),
    help="Output format (table or json)",
)
def get_question(
    tenant_id: Optional[str],
    assessment_id: str,
    question_id: str,
    output: Optional[str] = None,
) -> None:
    """Get details of a specific question.

    If --tenant-id is not provided, uses the default tenant configured with 'auth configure'.
    """
    try:
        # Get output format from context if set via global option
        ctx = click.get_current_context()
        ctx_output = ctx.obj.get("output_format") if ctx.obj else None
        output_format = output or ctx_output

        session = Session()

        # Get tenant ID from provided value or session default
        tenant_id = get_tenant_id(session, tenant_id)
        if not tenant_id:
            return

        # Call the client method with explicit parameters
        result = session.assessment.get_question(tenant_id, assessment_id, question_id)

        # Format the output based on the selected format
        if output_format and output_format.lower() == "json":
            # Convert to a dictionary for JSON output
            question_data: dict[str, Any] = {
                "id": result.id,
                "title": result.title,
                "description": result.description,
                "pillar_id": result.pillar_id,
                "pillar_name": result.pillar_name,
                "is_answered": result.is_answered,
                "status": "Answered" if result.is_answered else "Not Answered",
                "risk": result.risk if result.is_answered else "UNANSWERED",
            }

            # Add answer-related fields if the question is answered
            if result.is_answered:
                question_data["reason"] = result.reason or "NONE"
                question_data["notes"] = result.notes or ""

                # Add selected choices
                if result.selected_choices or result.choice_answers:
                    choice_ids = result.selected_choices or result.choice_answers
                    selected_choices = []

                    for choice_id in choice_ids:
                        # Handle both string and dictionary formats for choice_answers
                        if isinstance(choice_id, dict) and "ChoiceId" in choice_id:
                            choice_id = choice_id["ChoiceId"]

                        # Find the choice title if available
                        choice_title = next(
                            (
                                choice["Title"]
                                for choice in result.choices
                                if choice["ChoiceId"] == choice_id
                            ),
                            "Unknown",
                        )
                        selected_choices.append(
                            {"id": choice_id, "title": choice_title}
                        )

                    question_data["selected_choices"] = selected_choices

            # Add available choices
            if result.choices:
                question_data["choices"] = (
                    [
                        {
                            "id": choice.get("ChoiceId"),
                            "title": choice.get("Title"),
                            "description": choice.get("Description", ""),
                        }
                        for choice in result.choices
                    ]
                    if result.choices
                    else []
                )

            # Output as JSON
            console.print(json.dumps(question_data, indent=2))
        else:
            # Display question details in table format
            console.print(f"[bold]Question:[/bold] {result.title}")
            console.print(f"[bold]ID:[/bold] {result.id}")
            console.print(
                f"[bold]Pillar:[/bold] {result.pillar_name} ({result.pillar_id})"
            )
            console.print(f"[bold]Description:[/bold] {result.description}")

            # Show status and risk information
            status = (
                "[green]Answered[/green]"
                if result.is_answered
                else "[yellow]Not Answered[/yellow]"
            )
            console.print(f"[bold]Status:[/bold] {status}")

            if result.is_answered:
                console.print(f"[bold]Risk:[/bold] {result.risk or 'Not specified'}")
                console.print(f"[bold]Reason:[/bold] {result.reason or 'Not provided'}")
                if result.notes:
                    console.print(f"[bold]Notes:[/bold] {result.notes}")

                if result.selected_choices or result.choice_answers:
                    console.print("\n[bold]Selected Choices:[/bold]")
                    # Use selected_choices or choice_answers, whichever is available
                    choice_ids = result.selected_choices or result.choice_answers

                    for choice_id in choice_ids:
                        # Handle both string and dictionary formats for choice_answers
                        if isinstance(choice_id, dict) and "ChoiceId" in choice_id:
                            choice_id = choice_id["ChoiceId"]

                        # Find the choice title if available
                        choice_title = next(
                            (
                                choice["Title"]
                                for choice in result.choices
                                if choice["ChoiceId"] == choice_id
                            ),
                            "Unknown",
                        )
                        console.print(f"  • {choice_title} ({choice_id})")

            # Display available choices
            if result.choices:
                console.print("\n[bold]Available Choices:[/bold]")
                for choice in result.choices:
                    console.print(f"  • {choice['Title']} ({choice['ChoiceId']})")

        # Show hint for answering the question
        if not result.is_answered:
            console.print(
                "\n[dim]To answer this question, use the 'answer' command.[/dim]"
            )

    except Day2Error as e:
        console.print(format_error(e))


@assessment.command("answer")
@click.option("--tenant-id", help="ID of the tenant that owns the assessment")
@click.argument("assessment-id")
@click.argument("question-id")
@click.option(
    "--reason",
    type=click.Choice(
        [
            "OUT_OF_SCOPE",
            "BUSINESS_PRIORITIES",
            "ARCHITECTURE_CONSTRAINTS",
            "OTHER",
            "NONE",
        ]
    ),
    required=True,
    help="Reason for the answer",
)
@click.option("--choices", help="Comma-separated list of choice IDs to select")
@click.option("--notes", help="Additional notes for the answer")
@click.option(
    "--applicable/--not-applicable",
    default=True,
    help="Whether the question is applicable to the assessment",
)
def answer_question(
    tenant_id: Optional[str],
    assessment_id: str,
    question_id: str,
    reason: str,
    choices: Optional[str],
    notes: Optional[str],
    applicable: bool,
) -> None:
    """Answer a question in an assessment.

    If --tenant-id is not provided, uses the default tenant configured with 'auth configure'.

    ASSESSMENT-ID: ID of the assessment that contains the question.
    QUESTION-ID: ID of the question to answer.
    """
    try:
        session = Session()

        # Get tenant ID from provided value or session default
        tenant_id = get_tenant_id(session, tenant_id)
        if not tenant_id:
            return

        # Parse selected choices if provided and create choice_updates dictionary
        choice_updates = {}
        if choices:
            # First, try to get the question details to validate the choices
            try:
                question_details = session.assessment.get_question(
                    tenant_id, assessment_id, question_id
                )
                valid_choices = (
                    {
                        str(choice.get("ChoiceId", ""))
                        for choice in question_details.choices
                    }
                    if question_details.choices
                    else set()
                )

                # Process each choice ID
                for choice_id in [choice.strip() for choice in choices.split(",")]:
                    # Validate the choice ID if we have valid choices
                    if valid_choices and choice_id not in valid_choices:
                        console.print(
                            f"[yellow]Warning: Choice ID '{choice_id}' is not in the list of valid choices for this question.[/yellow]"
                        )
                        console.print(
                            f"[yellow]Valid choices are: {', '.join(valid_choices)}[/yellow]"
                        )

                    # Add the choice to the updates dictionary
                    choice_updates[choice_id] = {"Status": "SELECTED"}
            except Day2Error as e:
                # If we can't get the question details, just use the provided choices
                console.print(
                    f"[yellow]Warning: Could not validate choice IDs: {e}[/yellow]"
                )
                for choice_id in [choice.strip() for choice in choices.split(",")]:
                    choice_updates[choice_id] = {"Status": "SELECTED"}

        # Create the answer input with the new format
        answer_data = AnswerQuestionInput(
            LensAlias="wellarchitected",
            ChoiceUpdates=choice_updates,
            Reason=reason,
            Notes=notes or "",
            IsApplicable=applicable,
        )

        # Submit the answer
        result = session.assessment.answer_question(
            tenant_id, assessment_id, question_id, answer_data
        )

        # Display result
        console.print(f"[green]{result.message}[/green]")
        console.print(f"[bold]Status:[/bold] {result.status}")
        console.print(f"[bold]Question ID:[/bold] {result.id}")

        # Show a summary of what was submitted
        console.print("\n[bold]Answer Summary:[/bold]")
        if choices:
            console.print(f"[bold]Selected Choices:[/bold] {choices}")
        console.print(f"[bold]Reason:[/bold] {reason}")
        if notes:
            console.print(f"[bold]Notes:[/bold] {notes}")
        if not applicable:
            console.print(
                "[bold]Applicability:[/bold] Not applicable to this assessment"
            )

        console.print(
            "\n[dim]To view the updated question details, use the 'question' command.[/dim]"
        )

    except Day2Error as e:
        console.print(format_error(e))


@assessment.command("findings")
@click.option("--tenant-id", help="ID of the tenant that owns the assessment")
@click.argument("assessment-id")
@click.option(
    "--severity",
    multiple=True,
    help="Filter by severity (HIGH, MEDIUM, LOW) (can be used multiple times)",
)
@click.option(
    "--status",
    multiple=True,
    help="Filter by status (OPEN, RESOLVED, SUPPRESSED) (can be used multiple times)",
)
@click.option(
    "--account",
    multiple=True,
    help="Filter by account number (can be used multiple times)",
)
@click.option(
    "--region", multiple=True, help="Filter by region code (can be used multiple times)"
)
@click.option(
    "--resource-type",
    multiple=True,
    help="Filter by resource type (can be used multiple times)",
)
@click.option(
    "--question-id",
    multiple=True,
    help="Filter by question ID (can be used multiple times)",
)
@click.option(
    "--resource-id",
    multiple=True,
    help="Filter by resource ID (can be used multiple times)",
)
@click.option(
    "--pillar-id",
    multiple=True,
    help="Filter by pillar ID (can be used multiple times)",
)
@click.option("--page-token", help="Page token for pagination")
@click.option("--page-size", type=int, default=10, help="Page size")
@click.option(
    "--output",
    type=click.Choice(["table", "json"], case_sensitive=False),
    help="Output format (table or json)",
)
def list_findings(
    tenant_id: Optional[str],
    assessment_id: str,
    severity: Tuple[str, ...],
    status: Tuple[str, ...],
    account: Tuple[str, ...],
    region: Tuple[str, ...],
    resource_type: Tuple[str, ...],
    question_id: Tuple[str, ...],
    resource_id: Tuple[str, ...],
    pillar_id: Tuple[str, ...],
    page_token: Optional[str],
    page_size: int,
    output: Optional[str] = None,
    check_id: Tuple[str, ...] = (),
    best_practice_id: Tuple[str, ...] = (),
    best_practice_risk: Tuple[str, ...] = (),
) -> None:
    """List findings for an assessment.

    If --tenant-id is not provided, uses the default tenant configured with 'auth configure'.

    ASSESSMENT-ID: ID of the assessment to list findings for.
    """
    try:
        # Get output format from context if set via global option
        ctx = click.get_current_context()
        ctx_output = ctx.obj.get("output_format") if ctx.obj else None
        output_format = output or ctx_output

        session = Session()

        # Get tenant ID from provided value or session default
        tenant_id = get_tenant_id(session, tenant_id)
        if not tenant_id:
            return

        # Call the client method with explicit parameters
        result = session.assessment.list_findings(
            tenant_id=tenant_id,
            assessment_id=assessment_id,
            status=list(status) if status else None,
            severity=list(severity) if severity else None,
            account_number=list(account) if account else None,
            region_code=list(region) if region else None,
            resource_type=list(resource_type) if resource_type else None,
            question_ids=list(question_id) if question_id else None,
            resource_ids=list(resource_id) if resource_id else None,
            pillar_ids=list(pillar_id) if pillar_id else None,
            page_token=page_token,
            page_size=page_size,
            check_ids=list(check_id) if check_id else None,
            best_practice_ids=list(best_practice_id) if best_practice_id else None,
            best_practice_risk=list(best_practice_risk) if best_practice_risk else None,
        )

        if not result.records:
            format_simple_output("No findings found.", format_override=output_format)
            return

        # Convert findings to a list of dictionaries for the formatter
        findings_data = []

        for finding in result.records:
            # Add finding to the list
            findings_data.append(
                {
                    "finding_id": finding.finding_id,
                    "title": finding.title,
                    "severity": finding.severity,
                    "status": finding.status,
                    "resource_type": finding.resource_type,
                    "account_number": finding.account_number,
                    "region_code": finding.region_code,
                    "pillar_id": finding.pillar_id,
                    "check_id": finding.check_id,
                    "best_practice_id": finding.best_practice_id,
                    "best_practice": finding.best_practice,
                    "best_practice_risk": finding.best_practice_risk,
                }
            )

        # Define column mapping for the formatter
        columns = {
            "finding_id": "Finding ID",
            "title": "Title",
            "severity": "Severity",
            "status": "Status",
            "resource_type": "Resource Type",
            "account_number": "Account",
            "region_code": "Region",
            "pillar_id": "Pillar ID",
            "check_id": "Check ID",
            "best_practice_id": "Best Practice ID",
            "best_practice": "Best Practice",
            "best_practice_risk": "Best Practice Risk",
        }

        # Format and output the results
        format_list_output(
            items=findings_data,
            title=f"Findings for Assessment: {assessment_id}",
            columns=columns,
            format_override=output_format,
        )

        # Display pagination information
        if result.next_page_token:
            format_simple_output(
                f"More results available. Use --page-token={result.next_page_token} to get the next page.",
                format_override=output_format,
            )

    except Day2Error as e:
        console.print(format_error(e))
