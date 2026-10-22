import { expect, test } from "@playwright/test";

test("lập lộ trình, xem giải trình, tư vấn chuyên ngành và báo cáo xung đột", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("student-sv01").click();
  await page.getByTestId("run-plan").click();

  await expect(page.getByTestId("term-grid")).toBeVisible();
  expect(await page.getByTestId("plan-tab").count()).toBeGreaterThanOrEqual(4);

  await page.getByTestId("course-card").first().click();
  await expect(page.getByTestId("explanation-drawer")).toContainText("Vì sao chọn");
  await page.getByRole("button", { name: "Đóng" }).click();

  await page.getByRole("link", { name: "So sánh phương án" }).first().click();
  await expect(page.getByTestId("metrics-table")).toBeVisible();

  await page.getByRole("link", { name: "Tư vấn chuyên ngành" }).first().click();
  await page.getByTestId("run-advisor").click();
  await expect(page.getByTestId("spec-card").first()).toBeVisible();

  await page.getByRole("link", { name: "Hồ sơ & tùy chọn" }).first().click();
  await page.getByTestId("student-sv04").click();
  await page.getByTestId("run-plan").click();
  await expect(page.getByTestId("conflict-report")).toContainText("Chuỗi tiên quyết");
});
