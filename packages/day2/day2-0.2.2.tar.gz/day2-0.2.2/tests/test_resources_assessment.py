"""Tests for the AssessmentClient."""

from unittest.mock import MagicMock, patch

import pytest

from day2.models.assessment import (
    AnswerQuestionInput,
    AnswerQuestionOutput,
    CreateAssessmentInput,
    CreateAssessmentOutput,
    Finding,
    GetAssessmentOutput,
    GetQuestionOutput,
    ListAssessmentsOutput,
    ListFindingsOutput,
    ListQuestionsOutput,
)
from day2.resources.assessment import AssessmentClient
from day2.session import Session


@pytest.fixture
def mock_session():
    """Create a mock session for testing."""
    session = MagicMock(spec=Session)
    # Add required attributes for BaseClient
    session._config = MagicMock()
    session._config.api_url = "https://api.example.com"
    session._config.api_version = "v1"
    return session


def test_list_assessments(mock_session):
    """Test listing assessments."""
    # Setup
    tenant_id = "tenant-123"
    status = "PENDING"
    mock_response = {
        "Assessments": [
            {
                "AssessmentId": "9d85dde75568c808c46e525ed88d993c",
                "AssessmentName": "Sandbox-1-Review",
                "Description": "Review for Sandbox1",
                "Status": "PENDING",
                "AssessmentArn": "arn:aws:wellarchitected:us-east-1:123456789012:workload/9d85dde75568c808c46e525ed88d993c",
                "Lenses": ["AWS Well-Architected Framework"],
                "TotalQuestions": 57,
                "AnsweredQuestions": 0,
                "CreatedAt": "2025-04-09T06:24:34",
                "UpdatedAt": "2025-04-09T06:24:34",
            }
        ],
        "NextPageToken": None,
    }

    # Set up the mock
    with patch.object(
        AssessmentClient, "_make_request", return_value=mock_response
    ) as mock_make_request:
        # Execute
        client = AssessmentClient(mock_session)
        result = client.list_assessments(tenant_id, status=status)

        # Verify
        mock_make_request.assert_called_once_with(
            "GET",
            f"tenants/{tenant_id}/assessments/",
            params={"Status": status, "PageSize": 10},
        )

    # Verify the result
    assert isinstance(result, ListAssessmentsOutput)
    assert len(result.assessments) == 1
    assert result.assessments[0].id == "9d85dde75568c808c46e525ed88d993c"
    assert result.assessments[0].name == "Sandbox-1-Review"
    assert result.assessments[0].description == "Review for Sandbox1"
    assert result.assessments[0].status == "PENDING"
    assert result.next_page_token is None


def test_list_assessments_with_keyword(mock_session):
    """Test listing assessments with keyword filter."""
    # Setup
    tenant_id = "tenant-123"
    status = "COMPLETED"
    keyword = "test"
    mock_response = {
        "Assessments": [],
        "NextPageToken": None,
    }

    # Set up the mock
    with patch.object(
        AssessmentClient, "_make_request", return_value=mock_response
    ) as mock_make_request:
        # Execute
        client = AssessmentClient(mock_session)
        result = client.list_assessments(tenant_id, status=status, keyword=keyword)

        # Verify
        mock_make_request.assert_called_once_with(
            "GET",
            f"tenants/{tenant_id}/assessments/",
            params={
                "Status": status,
                # "PageNumber": 1,  # Removed for token-based pagination
                "PageSize": 10,
                "Keyword": keyword,
            },
        )

    # Verify the result
    assert isinstance(result, ListAssessmentsOutput)
    assert len(result.assessments) == 0
    assert result.next_page_token is None


def test_get_assessment(mock_session):
    """Test getting an assessment by ID."""
    # Setup
    tenant_id = "tenant-123"
    assessment_id = "9d85dde75568c808c46e525ed88d993c"
    mock_response = {
        "AssessmentId": assessment_id,
        "AnsweredQuestions": 0,
        "CreatedAt": "2025-04-09T06:24:34",
        "Description": "Review for Sandbox1",
        "DiagramURL": None,
        "Environment": "PREPRODUCTION",
        "ImprovementStatus": "NOT_APPLICABLE",
        "InSync": 1,
        "Industry": "Primary_K_12",
        "IndustryType": "Education",
        "Lenses": ["AWS Well-Architected Framework"],
        "Owner": "test.user@example.com",
        "RegionCode": "us-east-1",
        "Status": "PENDING",
        "TotalQuestions": 57,
        "UpdatedAt": "2025-04-09T06:24:34",
        "AssessmentArn": "arn:aws:wellarchitected:us-east-1:123456789012:workload/9d85dde75568c808c46e525ed88d993c",
        "AssessmentName": "Sandbox-1-Review",
        "Scope": [
            {
                "AccountNumber": "111122223333",
                "Regions": ["ap-south-1", "us-east-1", "us-east-2"],
            },
            {"AccountNumber": "444455556666", "Regions": ["us-east-1", "us-east-2"]},
        ],
        "RiskCounts": {"High": 0, "Medium": 0},
        "LensAlias": "wellarchitected",
        "LensArn": "arn:aws:wellarchitected::aws:lens/wellarchitected",
        "LensVersion": "2025-02-25",
        "LensName": "AWS Well-Architected Framework",
        "LensStatus": "CURRENT",
        "AWSUpdatedAt": "2025-04-09T11:54:33+05:30",
        "LastRunAt": "2025-04-09T11:54:33+05:30",
        "ExecutionId": "9575dde75568c808c46e525ed88d9978",
    }

    # Set up the mock
    with patch.object(
        AssessmentClient, "_make_request", return_value=mock_response
    ) as mock_make_request:
        # Execute
        client = AssessmentClient(mock_session)
        result = client.get_assessment(tenant_id, assessment_id)

        # Verify
        mock_make_request.assert_called_once_with(
            "GET", f"tenants/{tenant_id}/assessments/{assessment_id}"
        )

    # Verify the result
    assert isinstance(result, GetAssessmentOutput)
    assert result.id == assessment_id
    assert result.name == "Sandbox-1-Review"
    assert result.description == "Review for Sandbox1"
    assert result.status == "PENDING"


def test_create_assessment(mock_session):
    """Test creating an assessment."""
    # Setup
    tenant_id = "tenant-123"
    assessment_data = CreateAssessmentInput(
        AssessmentName="Sandbox-1-Review",
        Description="Review for Sandbox1",
        ReviewOwner="test.user@example.com",
        Scope={
            "Project": {},
            "Accounts": [
                {
                    "AccountNumber": "111122223333",
                    "Regions": ["ap-south-1", "us-east-1", "us-east-2"],
                },
                {
                    "AccountNumber": "444455556666",
                    "Regions": ["us-east-1", "us-east-2"],
                },
            ],
        },
        Lenses=["AWS Well-Architected Framework"],
        RegionCode="us-east-1",
        Environment="PRODUCTION",
    )
    mock_response = {
        "AssessmentId": "9d85dde75568c808c46e525ed88d993c",
        "AnsweredQuestions": 0,
        "CreatedAt": "2025-04-09T06:24:34",
        "Description": "Review for Sandbox1",
        "DiagramURL": None,
        "Environment": "PREPRODUCTION",
        "ImprovementStatus": "NOT_APPLICABLE",
        "InSync": 1,
        "Industry": "Primary_K_12",
        "IndustryType": "Education",
        "Lenses": ["AWS Well-Architected Framework"],
        "Owner": "test.user@example.com",
        "RegionCode": "us-east-1",
        "Status": "PENDING",
        "TotalQuestions": 57,
        "UpdatedAt": "2025-04-09T06:24:34",
        "AssessmentArn": "arn:aws:wellarchitected:us-east-1:123456789012:workload/9d85dde75568c808c46e525ed88d993c",
        "AssessmentName": "Sandbox-1-Review",
        "Scope": [
            {
                "AccountNumber": "111122223333",
                "Regions": ["ap-south-1", "us-east-1", "us-east-2"],
            },
            {"AccountNumber": "444455556666", "Regions": ["us-east-1", "us-east-2"]},
        ],
        "RiskCounts": {"High": 0, "Medium": 0},
        "LensAlias": "wellarchitected",
        "LensArn": "arn:aws:wellarchitected::aws:lens/wellarchitected",
        "LensVersion": "2025-02-25",
        "LensName": "AWS Well-Architected Framework",
        "LensStatus": "CURRENT",
        "AWSUpdatedAt": "2025-04-09T11:54:33+05:30",
    }

    # Set up the mock
    with patch.object(
        AssessmentClient, "_make_request", return_value=mock_response
    ) as mock_make_request:
        # Execute
        client = AssessmentClient(mock_session)
        result = client.create_assessment(tenant_id, assessment_data)

        # Verify
        mock_make_request.assert_called_once_with(
            "POST",
            f"tenants/{tenant_id}/assessments/",
            json={
                "AssessmentName": "Sandbox-1-Review",
                "Description": "Review for Sandbox1",
                "ReviewOwner": "test.user@example.com",
                "Scope": {
                    "Project": {},
                    "Accounts": [
                        {
                            "AccountNumber": "111122223333",
                            "Regions": ["ap-south-1", "us-east-1", "us-east-2"],
                        },
                        {
                            "AccountNumber": "444455556666",
                            "Regions": ["us-east-1", "us-east-2"],
                        },
                    ],
                },
                "Lenses": ["AWS Well-Architected Framework"],
                "Tags": {},
                "RegionCode": "us-east-1",
                "Environment": "PRODUCTION",
            },
        )

    # Verify the result
    assert isinstance(result, CreateAssessmentOutput)
    assert result.id == "9d85dde75568c808c46e525ed88d993c"
    assert (
        result.assessment_arn
        == "arn:aws:wellarchitected:us-east-1:123456789012:workload/9d85dde75568c808c46e525ed88d993c"
    )


def test_list_questions(mock_session):
    """Test listing questions for an assessment pillar."""
    # Setup
    tenant_id = "tenant-123"
    assessment_id = "assessment-123"
    pillar_id = "security"

    mock_response = {
        "Questions": [
            {
                "QuestionId": "securely-operate",
                "QuestionTitle": "How do you securely operate your workload?",
                "PillarId": "security",
                "Reason": None,
                "Risk": "UNANSWERED",
            },
            {
                "QuestionId": "identities",
                "QuestionTitle": "How do you manage identities for people and machines?",
                "PillarId": "security",
                "Reason": None,
                "Risk": "UNANSWERED",
            },
        ]
    }

    # Set up the mock
    with patch.object(
        AssessmentClient, "_make_request", return_value=mock_response
    ) as mock_make_request:
        # Execute
        client = AssessmentClient(mock_session)
        result = client.list_questions(tenant_id, assessment_id, pillar_id)

        # Verify
        mock_make_request.assert_called_once_with(
            "GET",
            f"tenants/{tenant_id}/assessments/{assessment_id}/questions",
            params={"PillarId": pillar_id},
        )

    # Verify the result
    assert isinstance(result, ListQuestionsOutput)
    assert len(result.questions) == 2
    assert result.questions[0].id == "securely-operate"
    assert result.questions[0].title == "How do you securely operate your workload?"
    assert result.questions[0].pillar_id == "security"
    assert result.questions[0].risk == "UNANSWERED"
    assert result.questions[0].is_answered is False

    assert result.questions[1].id == "identities"
    assert (
        result.questions[1].title
        == "How do you manage identities for people and machines?"
    )

    # Verify the calculated fields
    assert result.pillar_id == "security"
    assert result.total_questions == 2
    assert result.answered_questions == 0


def test_get_question(mock_session):
    """Test getting a specific question."""
    # Setup
    tenant_id = "tenant-123"
    assessment_id = "assessment-123"
    question_id = "securely-operate"

    mock_response = {
        "QuestionTitle": "How do you securely operate your workload?",
        "QuestionDescription": "To securely operate your workload, you should apply overarching best practices to every area of security.",
        "PillarId": "security",
        "Risk": None,
        "Reason": None,
        "ChoiceAnswers": [],
        "Choices": [
            {
                "ChoiceId": "choice-1",
                "Title": "Implement security controls",
                "Description": "Implement security controls description",
            },
            {
                "ChoiceId": "choice-2",
                "Title": "Regularly review security posture",
                "Description": "Regularly review security posture description",
            },
        ],
        "HelpfulResourceUrl": "https://example.com/resources",
        "ImprovementPlanUrl": None,
        "IsApplicable": True,
    }

    # Set up the mock
    with patch.object(
        AssessmentClient, "_make_request", return_value=mock_response
    ) as mock_make_request:
        # Execute
        client = AssessmentClient(mock_session)
        result = client.get_question(tenant_id, assessment_id, question_id)

        # Verify
        mock_make_request.assert_called_once_with(
            "GET",
            f"tenants/{tenant_id}/assessments/{assessment_id}/questions/{question_id}",
        )

    # Verify the result
    assert isinstance(result, GetQuestionOutput)
    assert result.id == question_id  # ID is set in the client method
    assert result.title == "How do you securely operate your workload?"
    assert (
        result.description
        == "To securely operate your workload, you should apply overarching best practices to every area of security."
    )
    assert result.pillar_id == "security"
    assert result.pillar_name == "Security"  # Set in the client method
    assert result.risk is None
    assert result.reason is None
    assert result.helpful_resource_url == "https://example.com/resources"
    assert result.improvement_plan_url is None
    assert result.is_applicable is True
    assert result.choice_answers == []
    assert len(result.choices) == 2
    assert result.choices[0]["ChoiceId"] == "choice-1"
    assert result.choices[0]["Title"] == "Implement security controls"
    assert result.is_answered is False


def test_answer_question(mock_session):
    """Test answering a specific question."""
    # Setup
    tenant_id = "tenant-123"
    assessment_id = "assessment-123"
    question_id = "securely-operate"

    # Input data
    answer_data = AnswerQuestionInput(
        Reason="ARCHITECTURE_CONSTRAINTS",
        ChoiceUpdates={"choice-1": {"Status": "SELECTED"}},
        Notes="Need to follow up with the security team.",
        IsApplicable=True,
        LensAlias="wellarchitected",
    )

    # Mock response from API - using the new format with just a success message
    mock_response = {"Status": "Success", "Message": "Answer updated successfully"}

    # Set up the mock for _make_request
    with patch.object(
        AssessmentClient, "_make_request", return_value=mock_response
    ) as mock_make_request:
        # Execute
        client = AssessmentClient(mock_session)
        result = client.answer_question(
            tenant_id, assessment_id, question_id, answer_data
        )

        # Verify
        assert mock_make_request.call_count == 1
        call_args = mock_make_request.call_args
        assert call_args[0][0] == "PUT"
        assert (
            call_args[0][1]
            == f"tenants/{tenant_id}/assessments/{assessment_id}/questions/{question_id}"
        )

        # Check the JSON payload - should be direct, not wrapped
        json_payload = call_args[1]["json"]
        assert json_payload["Reason"] == "ARCHITECTURE_CONSTRAINTS"
        assert "choice-1" in json_payload["ChoiceUpdates"]
        assert json_payload["ChoiceUpdates"]["choice-1"]["Status"] == "SELECTED"
        assert json_payload["Notes"] == "Need to follow up with the security team."
        assert json_payload["IsApplicable"] == True
        assert json_payload["LensAlias"] == "wellarchitected"

    # Verify the result
    assert isinstance(result, AnswerQuestionOutput)
    assert result.id == question_id  # ID is set in the client method
    assert result.status == "Success"
    assert result.message == "Answer updated successfully"


def test_list_findings_with_string_params(mock_session):
    """Test listing findings for an assessment with string parameters."""
    # Setup
    tenant_id = "tenant-123"
    assessment_id = "assessment-123"
    severity = "HIGH"
    status = "OPEN"
    account_number = "123456789012"
    region_code = "us-east-1"
    resource_type = "AWS::EC2::Instance"
    page_size = 10
    page_token = "next-token-123"

    mock_response = {
        "Records": [
            {
                "FindingId": "finding-123",
                "ResourceId": "resource-123",
                "ResourceType": "AWS::EC2::Instance",
                "AccountNumber": "123456789012",
                "RegionCode": "us-east-1",
                "CheckId": "check-123",
                "Recommendation": "Implement security controls",
                "Remediation": True,
                "CreatedAt": "2023-01-01T00:00:00Z",
                "QuestionId": "securely-operate",
                "Question": "How do you securely operate your workload?",
                "PillarId": "security",
                "Severity": "HIGH",
                "Status": "OPEN",
                "Title": "Security Finding",
                "Description": "This is a security finding description.",
                "BestPracticeId": "sec_securely_operate_reduce_management_scope",
                "BestPractice": "Reduce security management scope",
                "BestPracticeRisk": "Medium",
            }
        ],
        "NextPageToken": "next-token-456",
    }

    # Set up the mock
    with patch.object(
        AssessmentClient, "_make_request", return_value=mock_response
    ) as mock_make_request:
        # Execute
        client = AssessmentClient(mock_session)
        result = client.list_findings(
            tenant_id=tenant_id,
            assessment_id=assessment_id,
            severity=severity,
            status=status,
            account_number=account_number,
            region_code=region_code,
            resource_type=resource_type,
            page_size=page_size,
            page_token=page_token,
        )

        # Verify
        mock_make_request.assert_called_once()
        call_args = mock_make_request.call_args[1]

        # Verify that string parameters are correctly passed
        assert call_args["params"]["Severity"] == severity
        assert call_args["params"]["Status"] == status
        assert call_args["params"]["AccountNumber"] == account_number
        assert call_args["params"]["RegionCode"] == region_code
        assert call_args["params"]["ResourceType"] == resource_type
        assert call_args["params"]["PageSize"] == str(page_size)
        assert call_args["params"]["PageToken"] == page_token

        # Verify that the URL is correct
        assert mock_make_request.call_args[0][0] == "GET"
        assert (
            mock_make_request.call_args[0][1]
            == f"tenants/{tenant_id}/assessments/{assessment_id}/findings"
        )

    # Verify the result
    assert isinstance(result, ListFindingsOutput)
    assert len(result.records) == 1
    assert result.records[0].finding_id == "finding-123"
    assert result.records[0].resource_id == "resource-123"
    assert result.records[0].resource_type == "AWS::EC2::Instance"
    assert result.records[0].account_number == "123456789012"
    assert result.records[0].region_code == "us-east-1"
    assert result.records[0].severity == "HIGH"
    assert result.records[0].status == "OPEN"
    assert result.records[0].title == "Security Finding"
    assert result.records[0].description == "This is a security finding description."
    assert (
        result.records[0].best_practice_id
        == "sec_securely_operate_reduce_management_scope"
    )
    assert result.records[0].best_practice == "Reduce security management scope"
    assert result.records[0].best_practice_risk == "Medium"
    assert result.next_page_token == "next-token-456"


def test_list_findings_with_array_params(mock_session):
    """Test listing findings for an assessment with array parameters."""
    # Setup
    tenant_id = "tenant-123"
    assessment_id = "assessment-123"
    severity = ["HIGH", "MEDIUM"]
    status = ["OPEN", "SUPPRESSED"]
    account_number = ["123456789012", "987654321098"]
    region_code = ["us-east-1", "us-west-2"]
    resource_type = ["AWS::EC2::Instance", "AWS::S3::Bucket"]
    question_ids = ["question-1", "question-2"]
    resource_ids = ["resource-1", "resource-2"]
    pillar_ids = ["security", "reliability"]
    page_size = 10

    mock_response = {
        "Records": [
            {
                "FindingId": "finding-123",
                "ResourceId": "resource-1",
                "ResourceType": "AWS::EC2::Instance",
                "AccountNumber": "123456789012",
                "RegionCode": "us-east-1",
                "CheckId": "check-123",
                "Recommendation": "Implement security controls",
                "Remediation": True,
                "CreatedAt": "2023-01-01T00:00:00Z",
                "QuestionId": "question-1",
                "Question": "How do you securely operate your workload?",
                "PillarId": "security",
                "Severity": "HIGH",
                "Status": "OPEN",
                "Title": "Security Finding",
                "Description": "This is a security finding description.",
                "BestPracticeId": "sec_securely_operate_reduce_management_scope",
                "BestPractice": "Reduce security management scope",
                "BestPracticeRisk": "Medium",
            }
        ],
        "NextPageToken": "next-token-456",
    }

    # Set up the mock
    with patch.object(
        AssessmentClient, "_make_request", return_value=mock_response
    ) as mock_make_request:
        # Execute
        client = AssessmentClient(mock_session)
        result = client.list_findings(
            tenant_id=tenant_id,
            assessment_id=assessment_id,
            severity=severity,
            status=status,
            account_number=account_number,
            region_code=region_code,
            resource_type=resource_type,
            question_ids=question_ids,
            resource_ids=resource_ids,
            pillar_ids=pillar_ids,
            page_size=page_size,
        )

        # Verify the params structure for array parameters
        mock_make_request.assert_called_once()
        call_args = mock_make_request.call_args[1]
        assert call_args["params"]["PageSize"] == str(page_size)

        # Check that array parameters are correctly passed
        # The helper function should convert these to lists in the params
        assert "Severity" in call_args["params"]
        assert "Status" in call_args["params"]
        assert "AccountNumber" in call_args["params"]
        assert "RegionCode" in call_args["params"]
        assert "ResourceType" in call_args["params"]
        assert "QuestionIds" in call_args["params"]
        assert "ResourceIds" in call_args["params"]
        assert "PillarIds" in call_args["params"]

        # Verify that the URL is correct
        assert mock_make_request.call_args[0][0] == "GET"
        assert (
            mock_make_request.call_args[0][1]
            == f"tenants/{tenant_id}/assessments/{assessment_id}/findings"
        )

    # Verify the result
    assert isinstance(result, ListFindingsOutput)
    assert len(result.records) == 1
    assert result.records[0].finding_id == "finding-123"
    assert result.records[0].resource_id == "resource-1"
    assert result.records[0].question_id == "question-1"
    assert result.records[0].pillar_id == "security"
    assert result.next_page_token == "next-token-456"
