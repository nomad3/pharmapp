import { render, screen } from '@testing-library/react';
import { HelmetProvider } from 'react-helmet-async';
import App from './App';

test('renders PharmApp homepage', () => {
  render(
    <HelmetProvider>
      <App />
    </HelmetProvider>
  );
  const heading = screen.getByText(/compara precios de medicamentos/i);
  expect(heading).toBeInTheDocument();
});
