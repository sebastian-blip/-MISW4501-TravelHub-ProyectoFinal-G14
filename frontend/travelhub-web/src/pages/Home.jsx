import Navbar from "../components/layout/Navbar";
import PageContainer from "../components/layout/PageContainer";
import ExploreSection from "../components/home/ExploreSection";
import FeaturedDestinations from "../components/home/FeaturedDestinations";
import Hero from "../components/home/Hero";
import "./Home.css";

function Home() {
  return (
    <div className="home-page">
      <Navbar />
      <Hero />
      <PageContainer>
        <ExploreSection />
        <FeaturedDestinations />
      </PageContainer>
    </div>
  );
}

export default Home;
