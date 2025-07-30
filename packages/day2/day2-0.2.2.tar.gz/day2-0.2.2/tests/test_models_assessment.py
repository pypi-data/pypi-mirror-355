"""Tests for the assessment models."""

import json
from datetime import datetime

import pytest

from day2.models.assessment import (
    AnswerQuestionInput,
    AnswerQuestionOutput,
    Assessment,
    CreateAssessmentInput,
    CreateAssessmentOutput,
    Finding,
    GetAssessmentOutput,
    GetQuestionOutput,
    ListAssessmentsOutput,
    ListFindingsOutput,
)


def test_assessment_parse():
    """Test parsing an Assessment from a dictionary."""
    data = {
        "AssessmentId": "assessment-123",
        "AssessmentName": "Test Assessment",
        "Description": "Test Description",
        "Status": "COMPLETED",
        "AssessmentArn": "arn:aws:wellarchitected:us-east-1:123456789012:workload/assessment-123",
        "Lenses": ["AWS Well-Architected Framework"],
        "TotalQuestions": 50,
        "AnsweredQuestions": 25,
    }

    assessment = Assessment.model_validate(data)

    assert assessment.id == "assessment-123"
    assert assessment.name == "Test Assessment"
    assert assessment.description == "Test Description"
    assert assessment.status == "COMPLETED"
    assert (
        assessment.assessment_arn
        == "arn:aws:wellarchitected:us-east-1:123456789012:workload/assessment-123"
    )
    assert assessment.lenses == ["AWS Well-Architected Framework"]
    assert assessment.total_questions == 50
    assert assessment.answered_questions == 25


def test_list_assessments_output_parse():
    """Test parsing a ListAssessmentsOutput from a dictionary."""
    data = {
        "Assessments": [
            {
                "AssessmentId": "assessment-123",
                "AssessmentName": "Test Assessment",
                "Description": "Test Description",
                "Status": "COMPLETED",
                "AssessmentArn": "arn:aws:wellarchitected:us-east-1:123456789012:workload/assessment-123",
                "Lenses": ["AWS Well-Architected Framework"],
                "TotalQuestions": 50,
                "AnsweredQuestions": 25,
            }
        ],
        "NextPageToken": "next-page-token",
    }

    list_output = ListAssessmentsOutput.model_validate(data)

    assert len(list_output.assessments) == 1
    assert list_output.next_page_token == "next-page-token"
    assessment = list_output.assessments[0]
    assert assessment.id == "assessment-123"
    assert assessment.name == "Test Assessment"
    assert assessment.description == "Test Description"
    assert assessment.status == "COMPLETED"


def test_create_assessment_input_serialization():
    """Test serializing a CreateAssessmentInput to a dictionary."""
    input_data = CreateAssessmentInput(
        AssessmentName="Test Assessment",
        Description="Test Description",
        ReviewOwner="user@example.com",
        Scope={
            "Project": {},
            "Accounts": [
                {"AccountNumber": "111122223333", "Regions": ["us-east-1", "us-east-2"]}
            ],
        },
        Lenses=["AWS Well-Architected Framework"],
        RegionCode="us-east-1",
        Environment="PRODUCTION",
    )

    data = input_data.model_dump(by_alias=True)

    assert data["AssessmentName"] == "Test Assessment"
    assert data["Description"] == "Test Description"
    assert data["ReviewOwner"] == "user@example.com"
    assert data["Scope"]["Project"] == {}
    assert len(data["Scope"]["Accounts"]) == 1
    assert data["Scope"]["Accounts"][0]["AccountNumber"] == "111122223333"
    assert "us-east-1" in data["Scope"]["Accounts"][0]["Regions"]
    assert data["Lenses"] == ["AWS Well-Architected Framework"]
    assert data["RegionCode"] == "us-east-1"
    assert data["Environment"] == "PRODUCTION"


def test_create_assessment_output_parse():
    """Test parsing a CreateAssessmentOutput from a dictionary."""
    data = {
        "AssessmentId": "assessment-123",
        "AssessmentName": "Test Assessment",
        "Description": "Test Description",
        "Status": "PENDING",
        "AssessmentArn": "arn:aws:wellarchitected:us-east-1:123456789012:workload/assessment-123",
        "Lenses": ["AWS Well-Architected Framework"],
        "TotalQuestions": 50,
        "AnsweredQuestions": 0,
    }

    output = CreateAssessmentOutput.model_validate(data)

    assert output.id == "assessment-123"
    assert (
        output.assessment_arn
        == "arn:aws:wellarchitected:us-east-1:123456789012:workload/assessment-123"
    )


def test_get_assessment_output_parse():
    """Test parsing a GetAssessmentOutput from a dictionary."""
    data = {
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
        "LastRunAt": "2025-04-09T06:24:34",
        "ExecutionId": "9575dde75568c808c46e525ed88d9978",
    }

    output = GetAssessmentOutput.model_validate(data)

    assert output.id == "9d85dde75568c808c46e525ed88d993c"
    assert output.name == "Sandbox-1-Review"
    assert output.description == "Review for Sandbox1"
    assert output.status == "PENDING"
    assert (
        output.assessment_arn
        == "arn:aws:wellarchitected:us-east-1:123456789012:workload/9d85dde75568c808c46e525ed88d993c"
    )
    assert output.created_at == datetime.fromisoformat("2025-04-09T06:24:34")
    assert output.updated_at == datetime.fromisoformat("2025-04-09T06:24:34")
    assert output.answered_questions == 0
    assert output.total_questions == 57
    assert output.lenses == ["AWS Well-Architected Framework"]
    assert output.owner == "test.user@example.com"
    assert output.diagram_url is None
    assert output.environment == "PREPRODUCTION"
    assert output.improvement_status == "NOT_APPLICABLE"
    assert output.in_sync == 1
    assert output.industry == "Primary_K_12"
    assert output.industry_type == "Education"
    assert output.region_code == "us-east-1"
    assert len(output.scope) == 2
    assert output.scope[0]["AccountNumber"] == "111122223333"
    assert output.scope[1]["AccountNumber"] == "444455556666"
    assert output.risk_counts == {"High": 0, "Medium": 0}
    assert output.lens_alias == "wellarchitected"
    assert output.lens_arn == "arn:aws:wellarchitected::aws:lens/wellarchitected"
    assert output.lens_version == "2025-02-25"
    assert output.lens_name == "AWS Well-Architected Framework"
    assert output.lens_status == "CURRENT"
    assert output.aws_updated_at == "2025-04-09T11:54:33+05:30"
    assert output.last_run_at == datetime.fromisoformat("2025-04-09T06:24:34")
    assert output.execution_id == "9575dde75568c808c46e525ed88d9978"


def test_get_question_output_parse():
    """Test parsing a GetQuestionOutput from a dictionary."""
    data = {
        "QuestionTitle": "How do you securely operate your workload?",
        "QuestionDescription": "To securely operate your workload, you should apply overarching best practices to every area of security.",
        "PillarId": "security",
        "Risk": "MEDIUM_RISK",
        "Reason": "We have implemented some security measures but need improvements.",
        "ChoiceAnswers": ["choice-1"],
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
        "Notes": "Need to follow up with the security team.",
    }

    # Set the ID manually as it would be done in the client method
    question_id = "securely-operate"
    output = GetQuestionOutput.model_validate(data)
    output.id = question_id

    # Set pillar_name manually as it would be done in the client method
    output.pillar_name = "Security"

    assert output.id == "securely-operate"
    assert output.title == "How do you securely operate your workload?"
    assert (
        output.description
        == "To securely operate your workload, you should apply overarching best practices to every area of security."
    )
    assert output.pillar_id == "security"
    assert output.pillar_name == "Security"
    assert output.risk == "MEDIUM_RISK"
    assert (
        output.reason
        == "We have implemented some security measures but need improvements."
    )
    assert output.notes == "Need to follow up with the security team."
    assert output.selected_choices == ["choice-1"]
    assert len(output.choices) == 2
    assert output.choices[0]["ChoiceId"] == "choice-1"
    assert output.choices[0]["Title"] == "Implement security controls"
    assert output.is_answered is True


def test_answer_question_input_serialization():
    """Test serializing an AnswerQuestionInput to a dictionary."""
    input_data = AnswerQuestionInput(
        Reason="ARCHITECTURE_CONSTRAINTS",
        ChoiceUpdates={
            "choice-1": {"Status": "SELECTED"},
            "choice-3": {"Status": "SELECTED"},
        },
        Notes="Need to follow up with the security team.",
        IsApplicable=True,
        LensAlias="wellarchitected",
    )

    data = input_data.model_dump(by_alias=True)

    assert data["Reason"] == "ARCHITECTURE_CONSTRAINTS"
    assert "choice-1" in data["ChoiceUpdates"]
    assert "choice-3" in data["ChoiceUpdates"]
    assert data["ChoiceUpdates"]["choice-1"]["Status"] == "SELECTED"
    assert data["Notes"] == "Need to follow up with the security team."
    assert data["IsApplicable"] == True
    assert data["LensAlias"] == "wellarchitected"


def test_answer_question_output_parse():
    """Test parsing an AnswerQuestionOutput from a dictionary."""
    # New API response format with Status and Message fields
    data = {"Status": "Success", "Message": "Answer updated successfully"}

    # Set the ID manually as it would be done in the client method
    question_id = "securely-operate"
    output = AnswerQuestionOutput.model_validate(data)
    output.id = question_id

    # Assert the fields from the API response
    assert output.status == "Success"
    assert output.message == "Answer updated successfully"
    assert output.id == "securely-operate"

    # Verify the model has the expected structure
    assert hasattr(output, "status")
    assert hasattr(output, "message")
    assert hasattr(output, "id")


def test_finding_parse():
    """Test parsing a Finding from a dictionary."""
    data = {
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

    finding = Finding.model_validate(data)

    assert finding.finding_id == "finding-123"
    assert finding.resource_id == "resource-123"
    assert finding.resource_type == "AWS::EC2::Instance"
    assert finding.account_number == "123456789012"
    assert finding.region_code == "us-east-1"
    assert finding.check_id == "check-123"
    assert finding.recommendation == "Implement security controls"
    assert finding.remediation is True
    assert finding.created_at == "2023-01-01T00:00:00Z"
    assert finding.question_id == "securely-operate"
    assert finding.question == "How do you securely operate your workload?"
    assert finding.pillar_id == "security"
    assert finding.severity == "HIGH"
    assert finding.status == "OPEN"
    assert finding.title == "Security Finding"
    assert finding.description == "This is a security finding description."


def test_list_findings_output_parse():
    """Test parsing a ListFindingsOutput from a dictionary."""
    data = {
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
            },
            {
                "FindingId": "finding-456",
                "ResourceId": "resource-456",
                "ResourceType": "AWS::S3::Bucket",
                "AccountNumber": "987654321098",
                "RegionCode": "us-west-2",
                "CheckId": "check-456",
                "Recommendation": "Enable bucket encryption",
                "Remediation": False,
                "CreatedAt": "2023-02-01T00:00:00Z",
                "QuestionId": "data-protection",
                "Question": "How do you protect your data?",
                "PillarId": "security",
                "Severity": "MEDIUM",
                "Status": "SUPPRESSED",
                "Title": "S3 Bucket Encryption",
                "Description": "S3 bucket is not encrypted.",
                "BestPracticeId": "sec_securely_operate_reduce_management_scope",
                "BestPractice": "Reduce security management scope",
                "BestPracticeRisk": "Medium",
            },
        ],
        "NextPageToken": "next-token-123",
    }

    output = ListFindingsOutput.model_validate(data)

    assert len(output.records) == 2
    assert output.next_page_token == "next-token-123"

    # Check first finding
    assert output.records[0].finding_id == "finding-123"
    assert output.records[0].resource_type == "AWS::EC2::Instance"
    assert output.records[0].severity == "HIGH"
    assert output.records[0].status == "OPEN"

    # Check second finding
    assert output.records[1].finding_id == "finding-456"
    assert output.records[1].resource_type == "AWS::S3::Bucket"
    assert output.records[1].severity == "MEDIUM"
    assert output.records[1].status == "SUPPRESSED"
