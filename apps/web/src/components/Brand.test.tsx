import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Brand } from "./Brand";

describe("Brand", () => {
  it("renders the product name accessibly", () => {
    render(<Brand />);
    expect(screen.getByLabelText("Growth Intelligence")).toBeInTheDocument();
  });
});
