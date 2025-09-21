// frontend/src/pages/EditorDashboard.js
// Назначение: ЛК редактора — очередь статей на модерацию.
// Путь: frontend/src/pages/EditorDashboard.js

import React from 'react';
import { fetchModerationQueue, reviewArticle } from '../Api';

export default function EditorDashboard() {
  const [items, setItems] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [notes, setNotes] = React.useState({});

  React.useEffect(() => {
    fetchModerationQueue()
      .then(setItems)
      .finally(() => setLoading(false));
  }, []);

  async function act(id, action) {
    await reviewArticle(id, action, notes[id] || '');
    setItems(prev => prev.filter(x => x.id !== id));
  }

  if (loading) return <div>Загрузка…</div>;

  return (
    <div className="card">
      <h2>Очередь модерации</h2>
      {items.length === 0 ? <div>Пусто</div> : null}
      {items.map(a => (
        <div key={a.id} className="card" style={{ marginTop: 8 }}>
          <div><b>{a.title}</b></div>
          <div dangerouslySetInnerHTML={{ __html: a.content }} style={{ opacity: .9, marginTop: 8 }} />
          <textarea
            placeholder="Заметки редактора"
            style={{ width: '100%', marginTop: 8, minHeight: 80 }}
            value={notes[a.id] || ''}
            onChange={e => setNotes(s => ({ ...s, [a.id]: e.target.value }))}
          />
          <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
            <button className="button" onClick={() => act(a.id, 'revise')}>На доработку</button>
            <button className="button primary" onClick={() => act(a.id, 'publish')}>Опубликовать</button>
          </div>
        </div>
      ))}
    </div>
  );
}

