import { parseRationale } from './rationale';

/** The real shape, from the stored rationales. Every one of 44 across two
 * different models carried Rating, Executive Summary, Investment Thesis and
 * Time Horizon; 38 also carried Price Target. */
const REAL = `**Rating**: Overweight

**Executive Summary**: The synthesis confirms a **structural asymmetry** for INTC.

**Investment Thesis**: The short-term thesis rests on holding support.

**Price Target**: 115.0

**Time Horizon**: 5 - 10 trading days (1-2 weeks)`;

describe('parseRationale', () => {
  it('splits the rationale into its labelled sections', () => {
    const parts = parseRationale(REAL);

    expect(parts.map((p) => p.label)).toEqual([
      'Rating',
      'Executive Summary',
      'Investment Thesis',
      'Price Target',
      'Time Horizon',
    ]);
    expect(parts[0].text).toBe('Overweight');
  });

  it('strips bold markers rather than printing them', () => {
    // The whole defect: the rationale is Markdown and was going into a
    // paragraph raw, so a reader saw the asterisks.
    const summary = parseRationale(REAL)[1].text;

    expect(summary).toContain('structural asymmetry');
    expect(summary).not.toContain('**');
  });

  it('keeps an unlabelled rationale rather than dropping it', () => {
    // Degrades safely: a shape nobody predicted still reaches the reader.
    const parts = parseRationale('Just a sentence, with no labels at all.');

    expect(parts).toHaveLength(1);
    expect(parts[0].label).toBe('');
    expect(parts[0].text).toContain('no labels');
  });

  it('folds a continuation paragraph into the section above it', () => {
    const parts = parseRationale('**Thesis**: One.\n\nA second paragraph.');

    expect(parts).toHaveLength(1);
    expect(parts[0].text).toContain('A second paragraph');
  });

  it('returns nothing for nothing', () => {
    expect(parseRationale('')).toEqual([]);
    expect(parseRationale(null)).toEqual([]);
  });
});
