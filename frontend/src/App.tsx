import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import LivePanel from "./pages/LivePanel";
import ProductCatalog from "./pages/ProductCatalog";
import Analytics from "./pages/Analytics";
import Activity from "./pages/Activity";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<LivePanel />} />
          <Route path="/products" element={<ProductCatalog />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/activity" element={<Activity />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
