import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  }

  render() {
    if (this.state.hasError) {
      const errorMessage = this.state.error?.message || 'Unknown error';
      
      return (
        <div className="min-h-screen bg-[#050505] flex items-center justify-center p-4">
          <div className="text-center max-w-md">
            <h1 className="font-anton text-4xl md:text-6xl text-white uppercase mb-4">
              <span className="text-[#FF0099]">Oops!</span>
            </h1>
            <p className="text-[#A1A1AA] mb-4">
              Something went wrong. Please try again.
            </p>
            <p className="text-[#666] text-xs mb-6 break-words">
              {errorMessage}
            </p>
            <div className="flex gap-3 justify-center">
              <button
                onClick={this.handleRetry}
                className="bg-[#333] hover:bg-[#444] text-white px-6 py-3 font-bold uppercase"
              >
                Try Again
              </button>
              <button
                onClick={() => window.location.reload()}
                className="bg-[#FF0099] hover:bg-[#e6008a] text-white px-6 py-3 font-bold uppercase"
              >
                Refresh Page
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
