import "./PageContainer.css";

function PageContainer({ children }) {
  return (
    <main className="page-container">
      <div className="page-container__inner">{children}</div>
    </main>
  );
}

export default PageContainer;
