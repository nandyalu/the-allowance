import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { AgentNote } from '../../core/models/api.models';
import { AgentService } from '../../core/services/agent.service';
import { NotesView } from './notes-view';

function note(over: Partial<AgentNote> = {}): AgentNote {
  return {
    id: 1,
    ran_at: '2026-09-03T13:35:00Z',
    reason: 'I cannot see sector data.',
    ...over,
  };
}

class AgentServiceStub {
  notes: AgentNote[] = [];
  fail = false;

  async getNotes(): Promise<AgentNote[]> {
    if (this.fail) throw new Error('network error');
    return this.notes;
  }
}

describe('NotesView', () => {
  let service: AgentServiceStub;

  beforeEach(async () => {
    service = new AgentServiceStub();
    await TestBed.configureTestingModule({
      imports: [NotesView],
      providers: [{ provide: AgentService, useValue: service }, provideRouter([])],
    }).compileComponents();
  });

  async function render(): Promise<HTMLElement> {
    const fixture = TestBed.createComponent(NotesView);
    await fixture.whenStable();
    return fixture.nativeElement as HTMLElement;
  }

  it('says there are no notes yet, rather than rendering nothing', async () => {
    const el = await render();
    expect(el.querySelector('.empty')?.textContent).toContain('No notes yet');
  });

  it('shows a note with its reason', async () => {
    service.notes = [note({ reason: 'I need a position-size cap.' })];
    const el = await render();
    expect(el.querySelector('.agent-note-text')?.textContent).toContain(
      'I need a position-size cap.',
    );
  });

  it('shows every note, not just the first', async () => {
    service.notes = [note({ id: 1, reason: 'first' }), note({ id: 2, reason: 'second' })];
    const el = await render();
    const texts = Array.from(el.querySelectorAll('.agent-note-text')).map((n) => n.textContent);
    expect(texts).toEqual(['first', 'second']);
  });

  it('says the notes could not be read when the fetch fails', async () => {
    service.fail = true;
    const el = await render();
    expect(el.querySelector('.empty')?.textContent).toContain('could not be read');
  });
});
