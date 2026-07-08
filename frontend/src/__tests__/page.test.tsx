import { render, screen } from "@testing-library/react";
import Home from "@/app/page";

describe("Home page", () => {
  it("renders the product name and roadmap areas", () => {
    render(<Home />);
    expect(
      screen.getByRole("heading", { name: "DocQuery AI" })
    ).toBeInTheDocument();
    expect(screen.getByText("Review")).toBeInTheDocument();
    expect(screen.getByText("Audit")).toBeInTheDocument();
  });
});
