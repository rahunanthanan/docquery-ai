"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

/** §9: global boundary — render failures never white-screen the app. */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("Unhandled render error", error, info);
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <main className="center-card">
          <h1>Something went wrong</h1>
          <p className="muted">The page hit an unexpected error.</p>
          <button
            className="button"
            onClick={() => this.setState({ hasError: false })}
          >
            Try again
          </button>
        </main>
      );
    }
    return this.props.children;
  }
}
