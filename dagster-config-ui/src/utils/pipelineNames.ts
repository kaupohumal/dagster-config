export const dagsterPipelineNamePattern = /^[A-Za-z0-9_]+$/;

export const pythonKeywords = new Set([
  'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 'break', 'class',
  'continue', 'def', 'del', 'elif', 'else', 'except', 'finally', 'for', 'from', 'global',
  'if', 'import', 'in', 'is', 'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return',
  'try', 'while', 'with', 'yield', 'match', 'case',
]);

export function getPipelineNameValidationError(pipelineName: string): string | null {
  const normalized = pipelineName.trim();
  if (!normalized) return 'Pipeline name is required.';
  if (!dagsterPipelineNamePattern.test(normalized)) {
    return 'Pipeline name must contain only letters, numbers, and underscores.';
  }
  if (pythonKeywords.has(normalized)) {
    return 'Pipeline name cannot be a Python keyword.';
  }
  return null;
}

