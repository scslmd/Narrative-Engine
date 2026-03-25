import { Component, ReactNode } from 'react';
import type { ErrorInfo } from '../types/error';
import Fallback from './Fallback';
import { logError } from '../lib/errorHandling';

interface Props {
  children: ReactNode;
  fallback?: (error: Error, errorInfo: ErrorInfo) => JSX.Element;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: {
        componentStack: '',
        errorMessage: error.message,
      },
    };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    logError(error, errorInfo);
    
    this.setState((prevState) => ({
      ...prevState,
      errorInfo: {
        ...prevState.errorInfo,
        componentStack: errorInfo.componentStack,
      },
    }));
  }

  private handleRetry = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  public render(): ReactNode {
    if (this.state.hasError && this.state.error && this.state.errorInfo) {
      const { fallback } = this.props;
      
      if (fallback) {
        return fallback(this.state.error, this.state.errorInfo);
      }

      return <Fallback error={this.state.error} errorInfo={this.state.errorInfo} onRetry={this.handleRetry} />;
    }

    return this.props.children;
  }
}
