import { Link, Route, Routes } from 'react-router-dom';
import { useUser } from './context/UserContext';
import TicketListPage from './pages/TicketListPage';
import TicketDetailPage from './pages/TicketDetailPage';
import CreateTicketPage from './pages/CreateTicketPage';

function Header() {
  const { users, currentUserId, setCurrentUserId } = useUser();

  return (
    <header className="header">
      <div className="header-inner">
        <Link to="/" className="logo">TicketDesk</Link>
        <div className="acting-as">
          <label htmlFor="acting-as-select">Acting as</label>
          <select
            id="acting-as-select"
            value={currentUserId || ''}
            onChange={(e) => setCurrentUserId(Number(e.target.value))}
          >
            {users.map((u) => (
              <option key={u.id} value={u.id}>{u.name} ({u.role})</option>
            ))}
          </select>
        </div>
      </div>
    </header>
  );
}

export default function App() {
  return (
    <>
      <Header />
      <main className="main">
        <Routes>
          <Route path="/" element={<TicketListPage />} />
          <Route path="/tickets/new" element={<CreateTicketPage />} />
          <Route path="/tickets/:id" element={<TicketDetailPage />} />
        </Routes>
      </main>
    </>
  );
}
