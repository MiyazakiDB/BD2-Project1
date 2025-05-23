import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Landing from './Landing';
import Register from './Register';
import TLogin from './TLogin';
import NavigationBar from './NavigationBar';
import QueryConsole from './QueryConsole';



export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<TLogin />} />
        <Route path="/register" element={<Register />} />
        <Route path="/navbar" element={<NavigationBar />} />
        <Route path="/query-console" element={<QueryConsole />} />
        {/* Add more routes as needed */}
      
      </Routes>
    </BrowserRouter>
  );
}