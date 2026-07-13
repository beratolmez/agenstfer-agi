import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "../../api";
import { Sources } from "./Sources";

afterEach(() => vi.restoreAllMocks());

describe("Sources", () => {
  it("previews, maps, and synchronizes a CSV through real UI actions", async () => {
    vi.spyOn(api, "sources").mockResolvedValue({ items: [] });
    vi.spyOn(api, "sourceSyncRuns").mockResolvedValue({ items: [] });
    vi.spyOn(api, "previewSourceFile").mockResolvedValue({
      source_id: "src-file-1",
      filename: "accounts.csv",
      bytes: 40,
      schema: { source_id: "src-file-1", entities: { accounts: ["id", "name"] } },
      preview: [
        {
          entity_type: "accounts",
          external_id: "acc-1",
          data: { id: "acc-1", name: "Atlas" },
          locator: { row: 2 },
        },
      ],
      warnings: [],
    });
    const mapSource = vi.spyOn(api, "mapSource").mockResolvedValue({});
    const syncSource = vi.spyOn(api, "syncSource").mockResolvedValue({ total_records: 1 });

    render(<Sources />);
    await screen.findByRole("heading", { name: "Veri Kaynakları" });

    const input = screen.getByLabelText(/CSV veya XLSX seçin/i);
    fireEvent.change(input, { target: { files: [new File(["id,name\nacc-1,Atlas"], "accounts.csv", { type: "text/csv" })] } });
    const uploadButton = screen.getByRole("button", { name: "Yükle ve önizle" });
    fireEvent.submit(uploadButton.closest("form")!);

    const mappingButton = await screen.findByRole("button", {
      name: "Mapping’i kaydet ve sync et",
    });
    fireEvent.click(mappingButton);

    await waitFor(() => expect(syncSource).toHaveBeenCalledWith("src-file-1"));
    expect(mapSource).toHaveBeenCalledWith("src-file-1", {
      entity_type: "accounts",
      field_mapping: { id: "id", name: "name" },
      classification: "internal",
    });
    expect(await screen.findByText(/1 kayıt immutable snapshot/i)).toBeVisible();
  });
});
