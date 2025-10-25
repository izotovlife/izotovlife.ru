import { render, screen } from "@testing-library/react";

// Подменяем тяжёлые компоненты-зависимости простыми заглушками,
// чтобы smoke-тест фокусировался на маршрутизации App.
jest.mock("./components/Navbar", () => () => (
  <nav data-testid="navbar">Навигация</nav>
));
jest.mock("./components/HeaderInfo", () => () => (
  <div data-testid="header-info">Информация</div>
));
jest.mock("./components/Footer", () => () => (
  <footer data-testid="footer">Подвал</footer>
));
jest.mock("./pages/FeedPage", () => () => (
  <main data-testid="feed-page">Лента</main>
));

import App from "./App";

test("отрисовывается шапка и главная страница по умолчанию", () => {
  render(<App />);
  expect(screen.getByTestId("navbar")).toHaveTextContent("Навигация");
  expect(screen.getByTestId("feed-page")).toHaveTextContent("Лента");
  expect(screen.getByTestId("footer")).toBeInTheDocument();
});
