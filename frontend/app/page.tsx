'use client';

import { useEffect, useState } from 'react';
import { Activity, BarChart3, Dna, Users } from 'lucide-react';
import Link from 'next/link';
import api, { StatsResponse } from '@/lib/api';

export default function Home() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      try {
        const data = await api.getStats();
        setStats(data);
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      } finally {
        setLoading(false);
      }
    }
    fetchStats();
  }, []);

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center space-y-8">
          {/* Logo and Title */}
          <div className="space-y-4">
            <div className="flex justify-center">
              <div className="p-4 bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl shadow-lg">
                <Dna className="w-12 h-12 text-white" />
              </div>
            </div>
            <h1 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              BioMedical GraphRAG
            </h1>
            <p className="text-xl md:text-2xl text-gray-600 max-w-3xl mx-auto">
              AI-powered research assistant for biomedical literature
            </p>
            <p className="text-lg text-gray-500 max-w-2xl mx-auto">
              Ask questions in natural language and get insights from thousands of biomedical papers,
              genes, and research data
            </p>
          </div>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/query"
              className="px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold text-lg shadow-lg hover:shadow-xl transition-all hover:scale-105"
            >
              Start Querying
            </Link>
            <a
              href="https://github.com/paul-data-ai/biomedical_graphrag"
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-4 bg-white border-2 border-gray-300 text-gray-700 rounded-lg font-semibold text-lg shadow hover:shadow-lg transition-all hover:scale-105"
            >
              View on GitHub
            </a>
          </div>

          {/* Stats Section */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto mt-16">
            <StatCard
              icon={<BarChart3 className="w-8 h-8" />}
              label="Papers"
              value={loading ? '...' : stats?.total_papers.toLocaleString() || '0'}
              color="blue"
            />
            <StatCard
              icon={<Dna className="w-8 h-8" />}
              label="Genes"
              value={loading ? '...' : stats?.total_genes.toLocaleString() || '0'}
              color="purple"
            />
            <StatCard
              icon={<Users className="w-8 h-8" />}
              label="Authors"
              value={loading ? '...' : stats?.total_authors.toLocaleString() || '0'}
              color="green"
            />
            <StatCard
              icon={<Activity className="w-8 h-8" />}
              label="Institutions"
              value={loading ? '...' : stats?.total_institutions.toLocaleString() || '0'}
              color="orange"
            />
          </div>
        </div>

        {/* Features Section */}
        <div className="mt-24 grid md:grid-cols-3 gap-8">
          <FeatureCard
            title="Natural Language Queries"
            description="Ask questions in plain English and get AI-powered answers from biomedical research"
            icon="💬"
          />
          <FeatureCard
            title="Knowledge Graph"
            description="Explore connections between papers, genes, authors, and institutions"
            icon="🔗"
          />
          <FeatureCard
            title="Vector Search"
            description="Find semantically similar research using advanced embedding models"
            icon="🔍"
          />
        </div>

        {/* Example Queries */}
        <div className="mt-24">
          <h2 className="text-3xl font-bold text-center mb-8 text-gray-800">
            Try Example Queries
          </h2>
          <div className="grid md:grid-cols-2 gap-4 max-w-4xl mx-auto">
            <ExampleQuery text="What are the latest findings on CRISPR gene editing?" />
            <ExampleQuery text="Who collaborates with Jennifer Doudna?" />
            <ExampleQuery text="Show me papers about TP53 gene mutations" />
            <ExampleQuery text="What genes are mentioned in cancer immunotherapy?" />
          </div>
        </div>

        {/* Tech Stack */}
        <div className="mt-24 text-center">
          <p className="text-gray-500 text-sm mb-4">Powered by</p>
          <div className="flex flex-wrap justify-center gap-4 text-sm text-gray-600">
            <span className="px-4 py-2 bg-white rounded-full shadow">Neo4j</span>
            <span className="px-4 py-2 bg-white rounded-full shadow">Qdrant</span>
            <span className="px-4 py-2 bg-white rounded-full shadow">OpenAI</span>
            <span className="px-4 py-2 bg-white rounded-full shadow">FastAPI</span>
            <span className="px-4 py-2 bg-white rounded-full shadow">Next.js</span>
            <span className="px-4 py-2 bg-white rounded-full shadow">Prefect</span>
          </div>
        </div>
      </div>
    </main>
  );
}

// Components
function StatCard({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: string; color: string }) {
  const colorClasses = {
    blue: 'from-blue-500 to-blue-600',
    purple: 'from-purple-500 to-purple-600',
    green: 'from-green-500 to-green-600',
    orange: 'from-orange-500 to-orange-600',
  }[color];

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
      <div className={`inline-flex p-3 rounded-lg bg-gradient-to-br ${colorClasses} text-white mb-4`}>
        {icon}
      </div>
      <div className="text-3xl font-bold text-gray-800">{value}</div>
      <div className="text-sm text-gray-500 mt-1">{label}</div>
    </div>
  );
}

function FeatureCard({ title, description, icon }: { title: string; description: string; icon: string }) {
  return (
    <div className="bg-white rounded-xl shadow-lg p-8 hover:shadow-xl transition-shadow">
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="text-xl font-bold text-gray-800 mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  );
}

function ExampleQuery({ text }: { text: string }) {
  return (
    <Link
      href={`/query?q=${encodeURIComponent(text)}`}
      className="block p-4 bg-white rounded-lg shadow hover:shadow-lg transition-all hover:scale-105 border border-gray-200"
    >
      <p className="text-gray-700">{text}</p>
    </Link>
  );
}
