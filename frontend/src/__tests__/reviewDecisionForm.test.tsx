/** §10: ReviewDecisionForm validation — comment rules per §6. */

import { fireEvent, render, screen } from "@testing-library/react";

import { ReviewDecisionForm } from "@/components/review/ReviewDecisionForm";
import type { AnswerStatus } from "@/lib/api/review";

const ALL: AnswerStatus[] = ["approved", "flagged", "rejected"];

function renderForm(allowed: AnswerStatus[] = ALL, onSubmit = jest.fn()) {
  render(
    <ReviewDecisionForm allowedDecisions={allowed} pending={false} onSubmit={onSubmit} />,
  );
  return onSubmit;
}

test("submit is disabled until a decision is chosen", () => {
  renderForm();
  expect(screen.getByRole("button", { name: "Submit decision" })).toBeDisabled();
  fireEvent.click(screen.getByRole("radio", { name: "Approve" }));
  expect(screen.getByRole("button", { name: "Submit decision" })).toBeEnabled();
});

test("approve needs no comment and submits null", () => {
  const onSubmit = renderForm();
  fireEvent.click(screen.getByRole("radio", { name: "Approve" }));
  fireEvent.click(screen.getByRole("button", { name: "Submit decision" }));
  expect(onSubmit).toHaveBeenCalledWith("approved", null);
});

test.each(["Flag", "Reject"])("%s requires a comment of at least 10 chars", (label) => {
  const onSubmit = renderForm();
  fireEvent.click(screen.getByRole("radio", { name: label }));
  const submit = screen.getByRole("button", { name: "Submit decision" });
  expect(submit).toBeDisabled();

  const comment = screen.getByPlaceholderText(/Explain the decision/);
  fireEvent.change(comment, { target: { value: "too short" } }); // 9 chars
  fireEvent.blur(comment);
  expect(submit).toBeDisabled();
  expect(screen.getByRole("alert")).toBeInTheDocument();

  fireEvent.change(comment, { target: { value: "this comment is long enough" } });
  expect(submit).toBeEnabled();
  fireEvent.click(submit);
  expect(onSubmit).toHaveBeenCalledWith(
    label === "Flag" ? "flagged" : "rejected",
    "this comment is long enough",
  );
});

test("only allowed decisions are offered", () => {
  renderForm(["approved", "rejected"]);
  expect(screen.getByRole("radio", { name: "Approve" })).toBeInTheDocument();
  expect(screen.getByRole("radio", { name: "Reject" })).toBeInTheDocument();
  expect(screen.queryByRole("radio", { name: "Flag" })).not.toBeInTheDocument();
});

test("terminal states render a notice instead of a form", () => {
  renderForm([]);
  expect(screen.getByText(/terminal state/)).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Submit decision" })).not.toBeInTheDocument();
});
