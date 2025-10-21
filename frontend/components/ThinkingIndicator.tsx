"use client";

import React from "react";

interface ThinkingIndicatorProps {
  text?: string;
  className?: string;
}

const ThinkingIndicator: React.FC<ThinkingIndicatorProps> = ({
  text = "Thinking",
  className = ""
}) => {
  return (
    <div className={`flex items-center gap-1 ${className}`}>
      <span className="text-gray-600">{text}</span>
      <div className="flex gap-1">
        <span
          className="inline-block w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce"
          style={{ animationDelay: "0ms", animationDuration: "1.4s" }}
        />
        <span
          className="inline-block w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce"
          style={{ animationDelay: "200ms", animationDuration: "1.4s" }}
        />
        <span
          className="inline-block w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce"
          style={{ animationDelay: "400ms", animationDuration: "1.4s" }}
        />
      </div>
    </div>
  );
};

export default ThinkingIndicator;