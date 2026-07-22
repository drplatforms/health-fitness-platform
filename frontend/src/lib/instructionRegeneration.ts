export function needsInstructionReplacementConfirmation(
  instructions: readonly string[] | null | undefined,
) {
  return Boolean(instructions?.length);
}

export function instructionReplacementConfirmationMessage(
  provider: string,
  model: string,
) {
  return `This will make another AI request using ${provider} / ${model} and overwrite the current instructions.`;
}
