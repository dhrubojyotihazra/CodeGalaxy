import React, { useEffect, useRef, useState, useCallback } from 'react';
import { 
  ArrowRight, 
  Loader2, 
  Github, 
  Zap, 
  Layers, 
  Code, 
  Bot, 
  User, 
  Star, 
  Check, 
  ChevronRight,
  Monitor,
  Cpu,
  Globe
} from 'lucide-react';
import { ingestRepo, getIngestStatus } from '../api/client';
import { parseGithubUrl } from '../utils/github';

// --- Sub-Components ---

const RedNoirBackground = () => (
    <div className="fixed inset-0 z-0 pointer-events-none selection-red">
        <div className="absolute inset-0 bg-gradient-to-b from-[#1a0505] to-black"></div>
        <div className="absolute top-0 left-0 w-[1px] h-[1px] bg-transparent stars-1 animate-[animStar_50s_linear_infinite]"></div>
        <div className="absolute top-0 left-0 w-[2px] h-[2px] bg-transparent stars-2 animate-[animStar_80s_linear_infinite]"></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-red-600/5 rounded-full blur-[120px]"></div>
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:40px_40px] [mask-image:radial-gradient(circle_at_center,black_40%,transparent_80%)]"></div>
    </div>
);

const Navbar = ({ onStartFlow }) => (
    <header className="fixed top-0 left-0 w-full z-50 pt-6 px-4">
        <nav className="max-w-5xl mx-auto flex items-center justify-between bg-black/60 backdrop-blur-xl border border-white/10 rounded-full px-6 py-3 shadow-2xl">
            <div className="flex items-center gap-2">
                <img src="/logo-icon.png" className="w-10 h-10 object-contain" alt="Logo" />
                <span className="text-lg font-bold font-manrope tracking-tight text-white uppercase">Code Galaxy</span>
            </div>
            
            <div className="hidden md:flex items-center gap-8">
                <a href="#features" className="text-xs font-bold uppercase tracking-widest text-zinc-400 hover:text-white transition-colors">Features</a>
                <a href="#testimonials" className="text-xs font-bold uppercase tracking-widest text-zinc-400 hover:text-white transition-colors">Testimonial</a>
            </div>

            <div className="flex items-center gap-4">
                {/* Enter Galaxy removed for cleaner Navbar aesthetics */}
            </div>
        </nav>
    </header>
);

const IngestForm = ({ onSubmit, loading, progress, error, onCancel }) => {
    const [repoUrl, setRepoUrl] = useState('');
    const [repoDetail, setRepoDetail] = useState(null);

    useEffect(() => {
        const detail = parseGithubUrl(repoUrl);
        setRepoDetail(detail);
    }, [repoUrl]);

    return (
        <form 
            onSubmit={(e) => { e.preventDefault(); if (repoDetail) onSubmit(repoDetail.owner, repoDetail.repo, repoDetail.branch, repoUrl); }} 
            className="w-full max-w-md mx-auto space-y-6 flex flex-col items-center animate-fade-up"
        >
            <div className="space-y-4 w-full text-left">
                {error && <div className="px-4 py-3 bg-red-500/10 border border-red-500/20 text-red-400 text-sm rounded-lg backdrop-blur-md">{error}</div>}
                <div className="relative group">
                    <input 
                        type="text" 
                        required 
                        disabled={loading} 
                        value={repoUrl} 
                        onChange={(e) => setRepoUrl(e.target.value)}
                        className="w-full px-6 py-4 bg-white/5 border border-white/10 rounded-full outline-none focus:border-[#ef233c] text-white placeholder-zinc-500 backdrop-blur-md transition-all font-mono text-sm"
                        placeholder="Paste GitHub Repository URL..." 
                    />
                    {repoDetail && !loading && (
                        <div className="absolute -bottom-6 left-6 text-[10px] text-[#ef233c] font-mono tracking-wider">
                            DETECTED: <span className="text-white">{repoDetail.owner}/{repoDetail.repo}</span>
                        </div>
                    )}
                </div>
            </div>
            {progress && (
                <div className="w-full space-y-2 px-6">
                    <div className="flex justify-between text-[10px] text-white/50 font-mono tracking-wider uppercase"><span>{progress.status}</span></div>
                    <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
                        <div className="h-full bg-[#ef233c] transition-all duration-300" style={{ width: `${progress.progress || 0}%` }} />
                    </div>
                </div>
            )}
            <div className="flex items-center gap-6 w-full pt-4 px-2">
                <button type="button" onClick={onCancel} disabled={loading} className="flex-1 text-zinc-400 hover:text-white px-6 py-3 transition-colors uppercase tracking-widest text-[10px] font-bold">
                    Back
                </button>
                <button type="submit" disabled={loading || !repoDetail} className="flex-[2] shiny-cta">
                    <span className="relative z-10 flex items-center gap-2 text-white text-xs font-bold uppercase tracking-widest">
                        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : null} 
                        {loading ? 'Analyzing' : 'Generate Universe'}
                    </span>
                </button>
            </div>
        </form>
    );
}

const Hero = ({ onStartFlow, showForm, handleIngest, loading, error, progress, onCancel }) => (
    <section className="min-h-screen flex flex-col items-center justify-center pt-32 pb-20 px-6">
        <div className="text-center max-w-5xl mx-auto">

            <h1 className="text-5xl md:text-8xl font-semibold tracking-tighter font-manrope leading-[1.1] mb-8 animate-fade-up" style={{ animationDelay: '0.2s' }}>
                <span className="block text-transparent bg-clip-text bg-gradient-to-b from-white via-white to-white/40">Code Intelligence</span>
                <span className="block text-transparent bg-clip-text bg-gradient-to-b from-white via-white to-white/40">
                    for the <span className="text-[#ef233c] inline-block relative">
                        Universe
                        <svg className="absolute w-full h-3 -bottom-2 left-0 text-[#ef233c] opacity-60" viewBox="0 0 100 10" preserveAspectRatio="none">
                            <path d="M0 5 Q 50 10 100 5" stroke="currentColor" strokeWidth="2" fill="none" />
                        </svg>
                    </span>
                </span>
            </h1>

            <p className="text-xl md:text-2xl text-zinc-400 max-w-2xl mx-auto mb-12 leading-relaxed animate-fade-up" style={{ animationDelay: '0.3s' }}>
                Map your architectural complexitiy. Visualize dependencies, hunt technical debt, and understand your systems in interactive 3D.
            </p>

            <div className="flex flex-col md:flex-row items-center justify-center gap-6 animate-fade-up w-full max-w-md mx-auto md:max-w-none px-4 md:px-0" style={{ animationDelay: '0.4s' }}>
                {!showForm ? (
                    <button onClick={onStartFlow} className="shiny-cta group">
                        <span className="relative z-10 flex items-center gap-2 text-white text-xs font-bold uppercase tracking-widest whitespace-nowrap">
                            Start Creating <ArrowRight className="transition-transform group-hover:translate-x-1" />
                        </span>
                    </button>
                ) : (
                    <IngestForm onSubmit={handleIngest} loading={loading} progress={progress} error={error} onCancel={onCancel} />
                )}
                
                {!showForm && (
                  <a 
                    href="https://github.com/dhrubojyotihazra/CodeGalaxy" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="group px-8 py-4 w-full md:w-auto rounded-full bg-zinc-900 border border-zinc-800 text-zinc-300 text-xs font-bold uppercase tracking-widest hover:text-white hover:bg-zinc-800 transition-all flex items-center justify-center gap-2"
                  >
                      <Github className="w-5 h-5" />
                      View on GitHub
                  </a>
                )}
            </div>
        </div>

        {/* Logo Strip */}
        <div className="w-full mt-32 border-y border-white/5 bg-white/[0.02] backdrop-blur-sm py-10 opacity-60 hover:opacity-100 transition-opacity">
            <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center gap-8 md:gap-16">
                <p className="text-[10px] font-bold tracking-[0.3em] text-zinc-500 uppercase shrink-0">Integrated with:</p>
                <div className="flex flex-wrap justify-center gap-8 md:gap-16 items-center w-full">
                    <div className="flex items-center gap-2 font-manrope font-semibold text-xs text-white/70"><div className="w-2 h-2 bg-red-500 rounded-full"></div>GITHUB</div>
                    <div className="flex items-center gap-2 font-manrope font-semibold text-xs text-white/70"><div className="w-2 h-2 bg-red-500 rounded-full"></div>THREE.JS</div>
                    <div className="flex items-center gap-2 font-manrope font-semibold text-xs text-white/70"><div className="w-2 h-2 bg-red-500 rounded-full"></div>GROQ AI</div>
                    <div className="flex items-center gap-2 font-manrope font-semibold text-xs text-white/70"><div className="w-2 h-2 bg-red-500 rounded-full"></div>RADIX UI</div>
                    <div className="flex items-center gap-2 font-manrope font-semibold text-xs text-white/70"><div className="w-2 h-2 bg-red-500 rounded-full"></div>LUCIDE</div>
                </div>
            </div>
        </div>
    </section>
);

const BentoGrid = () => (
    <section id="features" className="py-32 px-6">
        <div className="max-w-7xl mx-auto">
            <div className="mb-20 text-center max-w-3xl mx-auto animate-fade-up">
                <h2 className="text-4xl md:text-5xl font-semibold text-white tracking-tight font-manrope mb-6 uppercase">
                    The OS for <br />
                    <span className="text-[#ef233c] tracking-[0.1em]">Stellar Architecture</span>
                </h2>
                <p className="text-lg text-zinc-400 font-light">
                    Replace fragmented legacy maps with a cohesive platform driven by planetary visualization.
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 h-auto lg:h-[700px]">
                {/* Main Feature Card */}
                <div className="lg:col-span-2 lg:row-span-2 group relative overflow-hidden p-8 border border-white/10 bg-gradient-to-b from-zinc-900/50 to-black hover:border-white/20 transition-all rounded-xl">
                    <div className="relative z-10 h-full flex flex-col">
                        <div className="mb-6 inline-flex p-3 rounded-lg bg-white/5 border border-white/10 text-[#ef233c]">
                            <Bot className="w-6 h-6" />
                        </div>
                        <h3 className="text-3xl font-semibold text-white font-manrope mb-4 tracking-tight uppercase">Intelligence Summaries</h3>
                        <p className="text-zinc-400 text-lg leading-relaxed">Instantly generate high-density technical analysis of your stellar systems. Groq-powered agents analyze primary responsibilities and logic patterns in real-time.</p>
                        <div className="mt-auto flex items-center justify-between opacity-0 group-hover:opacity-100 transition-opacity transform translate-y-2 group-hover:translate-y-0">
                            <span className="text-xs font-mono font-bold text-[#ef233c] tracking-widest">EXPLORE LINK</span>
                            <ArrowRight className="w-4 h-4 text-[#ef233c]" />
                        </div>
                    </div>
                    <div className="absolute inset-0 opacity-0 group-hover:opacity-10 transition-opacity pointer-events-none" style={{ background: 'radial-gradient(circle at top right, #ef233c, transparent 70%)' }}></div>
                </div>

                {/* Feature 2 */}
                <div className="lg:col-span-2 group relative overflow-hidden p-8 border border-white/10 bg-black hover:border-white/20 transition-all rounded-xl">
                    <div className="relative z-10 flex flex-col h-full">
                        <div className="mb-4 inline-flex p-3 rounded-lg bg-white/5 border border-white/10 text-red-400">
                            <Zap className="w-6 h-6" />
                        </div>
                        <h3 className="text-2xl font-semibold text-white font-manrope mb-2 uppercase tracking-wide">Stellar Echo</h3>
                        <p className="text-zinc-400">Cinematic ripple expansion for planetary selection, providing immediate visual weight to your focal points.</p>
                    </div>
                    <div className="absolute inset-0 opacity-0 group-hover:opacity-10 transition-opacity pointer-events-none" style={{ background: 'radial-gradient(circle at top right, #ef233c, transparent 70%)' }}></div>
                </div>

                {/* Feature 3 */}
                <div className="group relative overflow-hidden p-8 border border-white/10 bg-black hover:border-white/20 transition-all rounded-xl">
                    <div className="relative z-10">
                        <div className="mb-4 inline-flex p-3 rounded-lg bg-white/5 border border-white/10 text-zinc-400">
                            <Layers className="w-6 h-6" />
                        </div>
                        <h3 className="text-xl font-semibold text-white font-manrope mb-2 uppercase">Topology</h3>
                        <p className="text-sm text-zinc-400">Map semantic relationships between file-planets with precision gravity links.</p>
                    </div>
                </div>

                {/* Feature 4 */}
                <div className="group relative overflow-hidden p-8 border border-white/10 bg-black hover:border-white/20 transition-all rounded-xl">
                    <div className="relative z-10">
                        <div className="mb-4 inline-flex p-3 rounded-lg bg-white/5 border border-white/10 text-white">
                            <Code className="w-6 h-6" />
                        </div>
                        <h3 className="text-xl font-semibold text-white font-manrope mb-2 uppercase">Source HUD</h3>
                        <p className="text-sm text-zinc-400">Real-time GitHub source uplink integrated directly into the HUD surface.</p>
                    </div>
                </div>
            </div>
        </div>
    </section>
);

const Testimonial = () => (
    <div id="testimonials" className="w-full bg-[#ef233c] py-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
            <div className="flex justify-center gap-1 text-black mb-6">
                {[1,2,3,4,5].map(i => <Star key={i} className="w-6 h-6" fill="currentColor" />)}
            </div>
            <h3 className="text-3xl md:text-5xl font-bold text-black font-manrope leading-tight mb-8">
                "CodeGalaxy was the most unique and innovative project in all of XiBit Hackathon"
            </h3>
            <div className="flex items-center justify-center gap-4">
                <div className="w-12 h-12 bg-black rounded-full flex items-center justify-center">
                    <User className="text-white w-6 h-6" />
                </div>
                <div className="text-center">
                    <div className="text-black font-bold text-lg">Mr. Amar Kumar Nath</div>
                    <div className="text-black/70 font-bold uppercase tracking-widest text-[10px]">Chief Executive Judge of XiBit</div>
                </div>
            </div>
        </div>
    </div>
);


const Footer = () => (
    <footer className="bg-black border-t border-zinc-900 pt-10 pb-10 relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-4 gap-12 mb-4 relative z-10">
            <div className="md:col-span-2">
                <div className="flex items-center gap-2 mb-6">
                    <img src="/logo-icon.png" className="w-12 h-12 object-contain" alt="Logo" />
                    <span className="text-2xl font-bold font-manrope tracking-tight text-white">CODE GALAXY</span>
                </div>
                <p className="text-zinc-500 max-w-xs leading-relaxed text-sm">Pioneering the future of architectural intelligence with planetary visualization and human-centered engineering principles.</p>
            </div>
            
            <div>
                <h4 className="text-[10px] font-bold text-[#ef233c] uppercase tracking-[0.3em] mb-6">Discovery</h4>
                <ul className="space-y-4 text-zinc-400 text-xs font-bold uppercase tracking-widest">
                    <li><a href="#features" className="hover:text-white transition-colors">Features</a></li>
                    <li><a href="#features" className="hover:text-white transition-colors">Intelligence</a></li>
                    <li><a href="https://github.com/dhrubojyotihazra/codegalaxy" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">Source Control</a></li>
                </ul>
            </div>
            
            <div>
                <h4 className="text-[10px] font-bold text-[#ef233c] uppercase tracking-[0.3em] mb-6">Station</h4>
                <ul className="space-y-4 text-zinc-400 text-xs font-bold uppercase tracking-widest">
                    <li><a href="#" className="hover:text-white transition-colors">About Station</a></li>
                    <li><a href="#" className="hover:text-white transition-colors">Missions</a></li>
                    <li><a href="#" className="hover:text-white transition-colors">Comm-Link</a></li>
                    <li><a href="#" className="hover:text-white transition-colors">Legal HUD</a></li>
                </ul>
            </div>
        </div>


        <div className="max-w-7xl mx-auto px-6 border-t border-zinc-900 pt-8 flex flex-col md:flex-row items-center justify-between text-zinc-600 text-[10px] uppercase tracking-[0.3em] font-bold">
            <p>&copy; 2024 CODE GALAXY INTEL. All rights reserved.</p>
            <div className="flex gap-6 mt-4 md:mt-0">
                <a href="#" className="hover:text-zinc-400">Twitter</a>
                <a href="#" className="hover:text-zinc-400">LinkedIn</a>
                <a href="#" className="hover:text-zinc-400">GitHub</a>
            </div>
        </div>
    </footer>
);

export default function LandingPage({ onSuccess }) {
    const [showForm, setShowForm] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [progress, setProgress] = useState(null);

    const handleIngest = async (owner, repo, branch = 'main', originalUrl) => {
        setLoading(true); setError(''); setProgress({ status: 'starting', progress: 0 });

        let result = null;
        const maxRetries = 4;
        
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                if (attempt > 1) {
                    setProgress({ status: `Waking up Stellar Engine (Hugging Face cold start, attempt ${attempt}/${maxRetries})...`, progress: 0 });
                }
                result = await ingestRepo(owner.trim(), repo.trim(), branch.trim());
                break; // Succeeded!
            } catch (err) {
                // If it's a 404 or specific validation error from backend, don't retry cold start
                if (err.response?.status === 404 || err.response?.data?.detail) {
                    setLoading(false);
                    setError(err.response?.data?.detail || 'Repository or branch not found.');
                    return;
                }
                // Network error or 503 from cold container
                if (attempt === maxRetries) {
                    setLoading(false);
                    setError('Backend server connection timed out. If Hugging Face Space was asleep, please try clicking Generate Universe again in 10 seconds.');
                    return;
                }
                // Wait 5s before retrying cold start
                await new Promise(r => setTimeout(r, 5000));
            }
        }

        if (!result) return;

        try {
            const repoId = result.repo_id;
            const pollInterval = setInterval(async () => {
                try {
                    const status = await getIngestStatus(repoId);
                    if (status) {
                        setProgress({ status: status.status, progress: status.progress });
                        if (status.status === 'done') {
                            clearInterval(pollInterval); setLoading(false);
                            onSuccess(repoId, originalUrl);
                        } else if (status.status === 'error') {
                            clearInterval(pollInterval); setLoading(false); setError('Ingestion failed during processing.');
                        }
                    }
                } catch { }
            }, 2000);
        } catch (err) {
            setLoading(false); setError(err.response?.data?.detail || 'Failed to poll ingestion status.');
        }
    };

    return (
        <div className="relative w-full min-h-screen bg-black text-white font-inter selection-red overflow-x-hidden pt-4">
            <RedNoirBackground />
            <Navbar onStartFlow={() => setShowForm(true)} />
            
            <main className="relative z-10">
                <Hero 
                    showForm={showForm} 
                    onStartFlow={() => setShowForm(true)} 
                    handleIngest={handleIngest} 
                    loading={loading} 
                    error={error} 
                    progress={progress} 
                    onCancel={() => setShowForm(false)} 
                />
                
                <BentoGrid />
                <Testimonial />

                <section className="py-20 px-6 text-center bg-zinc-950/40 relative">
                    <div className="max-w-3xl mx-auto">
                        <h2 className="text-5xl md:text-7xl font-bold font-manrope mb-8 tracking-tighter uppercase px-4">
                            Ready to <span className="text-[#ef233c]">Build?</span>
                        </h2>
                        <p className="text-xl text-zinc-400 mb-12 uppercase tracking-widest text-sm font-bold opacity-60">
                            Join the galactic vanguard and visualize the next generation of software.
                        </p>
                        
                        <div className="max-w-md mx-auto">
                           <button 
                             onClick={() => {
                               window.scrollTo({ top: 0, behavior: 'smooth' });
                               setShowForm(true);
                             }}
                             className="shiny-cta px-12 py-5"
                           >
                             <span className="relative z-10 text-white font-bold uppercase tracking-widest text-xs">Initialize Universe</span>
                           </button>
                        </div>
                    </div>
                </section>
            </main>

            <Footer />
        </div>
    );
}
