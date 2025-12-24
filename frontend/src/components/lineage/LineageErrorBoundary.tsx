import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { Result, Button } from 'antd';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

class LineageErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(_: Error): State {
    return { hasError: true };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Lineage Graph Error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <Result
          status="error"
          title="Visualization Failed"
          subTitle="Sorry, something went wrong while rendering the lineage graph."
          extra={[
            <Button type="primary" key="retry" onClick={() => this.setState({ hasError: false })}>
              Retry
            </Button>
          ]}
        />
      );
    }

    return this.props.children;
  }
}

export default LineageErrorBoundary;
