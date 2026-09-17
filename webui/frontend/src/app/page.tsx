'use client';

import { useState, useEffect } from 'react';
import { Trial, AgreementAnalysis, ReviewerDecomposition } from '@/lib/types';
import { TrialHeader } from '@/components/TrialHeader';
import { CriteriaNav } from '@/components/CriteriaNav';
import { AgreementComparisonTable } from '@/components/AgreementComparisonTable';
import { ConsensusPanel } from '@/components/ConsensusPanel';
import { apiClient } from '@/lib/api';

export default function HomePage() {
  const [trial, setTrial] = useState<Trial | null>(null);
  const [reviewers, setReviewers] = useState<string[]>([]);
  const [decompositions, setDecompositions] = useState<Record<string, ReviewerDecomposition>>({});
  const [agreement, setAgreement] = useState<AgreementAnalysis | null>(null);
  const [activeCriterionIndex, setActiveCriterionIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // For demo purposes, we'll use a hardcoded trial ID
  // In a real app, this would come from URL params or user selection
  const trialId = 'NCT03191786';

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);

        // Load all data for the trial
        const data = await apiClient.getCriteriaComparison(trialId);
        
        setTrial(data.trial);
        setReviewers(data.reviewers);
        setDecompositions(data.decompositions);
        setAgreement(data.agreement);
      } catch (err) {
        console.error('Failed to load data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [trialId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading trial data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="text-red-600 text-6xl mb-4">⚠️</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Error Loading Data</h1>
          <p className="text-gray-600 mb-4">{error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!trial || !agreement) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">No data available for trial {trialId}</p>
        </div>
      </div>
    );
  }

  const activeCriterion = trial.criteria[activeCriterionIndex];
  
  // Filter trait agreements for the active criterion
  // `trait_level` is not emitted by the current analysis schema, so treat it
  // as absent rather than crashing the page. See webui/README.md.
  const criterionTraitAgreements = (agreement.agreement_summary.trait_level ?? []).filter(
    traitAgreement => {
      // Check if any reviewer has this trait for the current criterion
      return reviewers.some(reviewer => {
        const reviewerTrial = decompositions[reviewer]?.[trialId];
        if (!reviewerTrial) return false;
        
        const matchingCriterion = reviewerTrial.criteria.find(
          c => c.original_text === activeCriterion.original_text
        );
        if (!matchingCriterion) return false;
        
        return matchingCriterion.traits.some(trait => {
          const signature = `${trait.trait}|${trait.category}|${trait.value}`;
          return signature === traitAgreement.trait_signature;
        });
      });
    }
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-6">
        {/* Header */}
        <TrialHeader trial={trial} reviewers={reviewers} />
        
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Navigation Sidebar */}
          <div className="lg:col-span-1">
            <CriteriaNav
              criteria={trial.criteria}
              activeCriterionIndex={activeCriterionIndex}
              onCriterionSelect={setActiveCriterionIndex}
            />
          </div>
          
          {/* Main Content */}
          <div className="lg:col-span-3 space-y-6">
            {/* Reviewer Comparison Table */}
            <AgreementComparisonTable
              criterion={activeCriterion}
              reviewers={reviewers}
              decompositions={decompositions}
              traitAgreements={criterionTraitAgreements}
              trialId={trialId}
            />
            
            {/* Consensus Panel */}
            <div>
              <h2 className="text-xl font-semibold mb-4">
                Consensus Analysis for Current Criterion
              </h2>
              <ConsensusPanel
                traitAgreements={criterionTraitAgreements}
                overallSummary={agreement.agreement_summary.overall}
              />
            </div>
          </div>
        </div>
        
        {/* Footer */}
        <footer className="mt-12 pt-6 border-t border-gray-200 text-center text-sm text-gray-500">
          <p>
            Clinical Trial Criteria Decomposition Agreement Analysis • 
            Powered by Fleiss&apos; Kappa Inter-rater Reliability
          </p>
        </footer>
      </div>
    </div>
  );
}
