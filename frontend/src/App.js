import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [medicamentos, setMedicamentos] = useState([]);

  useEffect(() => {
    // Obtener medicamentos desde el backend a través del proxy
    axios.get('/medicamentos')
      .then(response => {
        setMedicamentos(response.data);
      })
      .catch(error => {
        console.error('Error al obtener medicamentos:', error);
      });
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Comparador de Medicamentos</h1>
        <h2>Lista de Medicamentos</h2>
        <ul>
          {medicamentos.map(med => (
            <li key={med.id}>
              <strong>{med.nombre}</strong>: {med.descripcion}
            </li>
          ))}
        </ul>
      </header>
    </div>
  );
}

export default App;
