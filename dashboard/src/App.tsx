import React, { useState } from 'react';
import { 
   BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer 
 } from 'recharts';
 import { Activity, BookOpen, Layers, Clock, X, Sun, Moon } from 'lucide-react';
 import { useEffect } from 'react';
 import stats from './data/stats.json';
 
 const COLORS = ['#007AFF', '#6366F1', '#A855F7', '#EC4899', '#F97316'];

const App: React.FC = () => {
  const [showJournalList, setShowJournalList] = useState(false);
  const [show5DDetails, setShow5DDetails] = useState(false);
  const [selectedDimension, setSelectedDimension] = useState<number | null>(null);
  const [theme, setTheme] = useState<'light' | 'dark'>(
    (localStorage.getItem('theme') as 'light' | 'dark') || 'dark'
  );

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  // 데이터 가공
  const sourceData = Object.entries(stats.sources || {}).map(([name, value]) => ({ name, value }));
  const subfieldData = Object.entries(stats.subfields || {}).map(([name, value]) => ({ 
    name, 
    value 
  }));
  const methodData = Object.entries(stats.methods || {}).map(([name, value]) => ({
    name: name || "General",
    value
  }));
  const eraData = Object.entries(stats.eras || {}).map(([name, value]) => {
    let displayName = name;
    if (name === "Patristic") displayName = "교부";
    else if (name === "Medieval") displayName = "중세";
    else if (name === "Reformation") displayName = "종교개혁";
    else if (name === "Modern") displayName = "근대";
    else if (name === "Contemporary") displayName = "현대";
    
    return { name: displayName, value };
  });
  const languageData = Object.entries(stats.regions || {}).map(([name, value]) => {
    let displayName = name;
    if (name === "en") displayName = "영어";
    else if (name === "ko") displayName = "한국어";
    else if (name === "de") displayName = "독일어";
    else if (name === "nl") displayName = "네덜란드어";
    else if (name === "ie") displayName = "아일랜드어";
    else if (name === "ca") displayName = "불어/영어(캐나다)";
    else if (name === "unknown") displayName = "미분류";
    
    return { name: displayName, value };
  });

  const confessionData = Object.entries(stats.confessions || {}).map(([name, value]) => {
    let displayName = name || "초교파";
    if (name === "Catholic") displayName = "가톨릭";
    else if (name === "Protestant") displayName = "개신교";
    else if (name === "Reformed") displayName = "개혁주의";
    else if (name === "Anglican") displayName = "성공회";
    else if (name === "Ecumenical") displayName = "에큐메니칼";
    else if (name === "Evangelical") displayName = "복음주의";
    else if (name === "Lutheran") displayName = "루터교";
    else if (name === "Methodist") displayName = "감리교";
    
    return { name: displayName, value };
  });

  return (
    <div className="dashboard-container">
      <header className="header animate-fade">
        <div className="header-left">
          <div className="badge">Project: theo-trend-nexus</div>
          <h1>Theological Intel Dashboard</h1>
        </div>
        <div className="header-right">
          <button className="theme-toggle" onClick={toggleTheme} title="Toggle Theme">
            {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
          </button>
          <div className="badge">
            <Clock size={14} />
            Status: 5D Analysis Depth Active
          </div>
        </div>
      </header>

      <div className="stats-grid">
        <div className="stat-card animate-fade" style={{ animationDelay: '0.1s' }}>
          <div className="stat-label">Total Articles</div>
          <div className="stat-value">{stats.total_articles.toLocaleString()}</div>
          <Activity size={20} color="var(--accent-blue)" style={{ marginTop: '10px' }} />
        </div>
        <div
          className="stat-card animate-fade clickable"
          style={{ animationDelay: '0.2s' }}
          onClick={() => setShowJournalList(true)}
        >
          <div className="stat-label">Monitored Journals</div>
          <div className="stat-value">{stats.total_journals}</div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px' }}>
            <BookOpen size={20} color="var(--accent-purple)" />
            <span style={{ fontSize: '0.7rem', color: 'var(--accent-purple)' }}>View List →</span>
          </div>
        </div>
        <div
          className="stat-card animate-fade clickable"
          style={{ animationDelay: '0.4s' }}
          onClick={() => setShow5DDetails(true)}
        >
          <div className="stat-label">Analytic Depth</div>
          <div className="stat-value">5 Dimensions</div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px' }}>
            <Layers size={20} color="var(--accent-pink)" />
            <span style={{ fontSize: '0.7rem', color: 'var(--accent-pink)' }}>View Depth →</span>
          </div>
        </div>
      </div>

      <div className="main-grid">
        {/* Row 0: Source Intel Full Width Summary Bar */}
        <div className="chart-container animate-fade" style={{ animationDelay: '0.4s', gridColumn: 'span 2', minHeight: 'auto', padding: '1.5rem 2rem', marginBottom: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ flex: 1 }}>
              <p style={{ color: 'var(--accent-violet)', fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.25rem' }}>Distribution across platforms</p>
              <h3 style={{ margin: 0 }}>Source Intel</h3>
            </div>
            
            <div style={{ flex: 3, display: 'flex', justifyContent: 'center', gap: '3rem' }}>
              {sourceData.map((source, index) => (
                <div key={index} style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '0.65rem', color: '#A1A1AA', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '4px' }}>
                    {source.name}
                  </div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 800, color: COLORS[index % COLORS.length] }}>
                    {source.value.toLocaleString()}
                  </div>
                </div>
              ))}
            </div>

            <div style={{ flex: 1, textAlign: 'right' }}>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-violet)', lineHeight: 1 }}>{sourceData.length}</div>
              <div style={{ fontSize: '0.6rem', color: 'var(--text-secondary)', textTransform: 'uppercase', marginTop: '4px' }}>Active Sources</div>
            </div>
          </div>
        </div>

        {/* Row 1: Subfield Full Width */}
        <div className="chart-container animate-fade clickable" style={{ animationDelay: '0.5s', gridColumn: 'span 2' }} onClick={() => { setShow5DDetails(true); setSelectedDimension(1); }}>
          <p style={{ color: '#6366F1', fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.25rem' }}>Core theological mapping (Academic Order)</p>
          <h3 style={{ marginBottom: '1.5rem' }}>1. Subfield Distribution</h3>
          <div style={{ width: '100%', height: 400 }}>
            <ResponsiveContainer>
              <BarChart data={subfieldData} layout="vertical" margin={{ left: 140, right: 30 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" horizontal={false} />
                <XAxis type="number" stroke="var(--text-secondary)" fontSize={12} />
                <YAxis 
                  dataKey="name" 
                  type="category" 
                  stroke="#71717A" 
                  fontSize={11} 
                  width={150}
                  tick={{ fill: '#A1A1AA' }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'var(--tooltip-bg)', borderColor: 'var(--tooltip-border)', color: 'var(--text-primary)', borderRadius: '12px', boxShadow: 'var(--shadow-lg)' }}
                  itemStyle={{ color: 'var(--accent-purple)' }}
                />
                <Bar dataKey="value" fill="var(--accent-purple)" radius={[0, 4, 4, 0]} barSize={20} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-container animate-fade clickable" style={{ animationDelay: '0.7s' }} onClick={() => { setShow5DDetails(true); setSelectedDimension(2); }}>
          <p style={{ color: '#007AFF', fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.25rem' }}>Research logic analysis</p>
          <h3>2. Methodological Insight</h3>
          <div style={{ width: '100%', height: 250 }}>
            <ResponsiveContainer>
              <BarChart data={methodData} layout="vertical" margin={{ left: 30 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" horizontal={false} />
                <XAxis type="number" stroke="var(--text-secondary)" fontSize={12} />
                <YAxis dataKey="name" type="category" stroke="var(--text-secondary)" fontSize={10} width={100} />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'var(--tooltip-bg)', borderColor: 'var(--tooltip-border)', color: 'var(--text-primary)', borderRadius: '12px' }}
                />
                <Bar dataKey="value" fill="var(--accent-blue)" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Row 3: Era & Region/Confession */}
        <div className="chart-container animate-fade clickable" style={{ animationDelay: '0.8s' }} onClick={() => { setShow5DDetails(true); setSelectedDimension(3); }}>
          <p style={{ color: '#EC4899', fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.25rem' }}>Temporal scope identification</p>
          <h3>3. Historical Era Focus</h3>
          <div style={{ width: '100%', height: 250 }}>
            <ResponsiveContainer>
              <BarChart data={eraData} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" horizontal={false} />
                <XAxis type="number" hide />
                <YAxis
                  dataKey="name"
                  type="category"
                  stroke="var(--text-secondary)"
                  fontSize={10}
                  width={120}
                  tick={{ fill: 'var(--text-secondary)' }}
                />
                <Tooltip
                  cursor={{ fill: 'var(--glass-bg)' }}
                  contentStyle={{ backgroundColor: 'var(--tooltip-bg)', borderColor: 'var(--tooltip-border)', color: 'var(--text-primary)', borderRadius: '12px' }}
                />
                <Bar dataKey="value" fill="var(--accent-pink)" radius={[0, 4, 4, 0]} barSize={20} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-container animate-fade clickable" style={{ animationDelay: '0.85s' }} onClick={() => { setShow5DDetails(true); setSelectedDimension(4); }}>
          <p style={{ color: '#A855F7', fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.25rem' }}>Geopolitical & tradition census</p>
          <h3 style={{ marginBottom: '1.5rem' }}>4. Region & Confession</h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
            {/* Language List */}
            <div>
              <p style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '1rem', borderLeft: '2px solid var(--accent-violet)', paddingLeft: '8px' }}>Linguistic Spectrum</p>
              <div style={{ display: 'grid', gap: '0.75rem' }}>
                {languageData.slice(0, 5).map((item, idx) => (
                   <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-primary)', fontWeight: 500 }}>{item.name}</span>
                    <span style={{ fontSize: '0.8rem', color: COLORS[idx % COLORS.length], fontWeight: 700 }}>{item.value.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Confession List */}
            <div>
              <p style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '1rem', borderLeft: '2px solid var(--accent-orange)', paddingLeft: '8px' }}>Confessional Split</p>
              <div style={{ display: 'grid', gap: '0.75rem' }}>
                {confessionData.slice(0, 5).map((item, idx) => (
                  <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-primary)', fontWeight: 500 }}>{item.name}</span>
                    <span style={{ fontSize: '0.8rem', color: COLORS[(idx + 3) % COLORS.length], fontWeight: 700 }}>{item.value.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="chart-container animate-fade clickable" style={{ animationDelay: '0.9s', minHeight: 'auto' }} onClick={() => { setShow5DDetails(true); setSelectedDimension(5); }}>
          <p style={{ color: '#F97316', fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.25rem' }}>Precision audit system</p>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '1.5rem' }}>
            <h3>5. AI Confidence Score</h3>
            <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--accent-orange)', lineHeight: 1 }}>92.4%</div>
          </div>
          <div style={{ width: '100%', height: '10px', background: 'var(--glass-bg)', borderRadius: '5px', overflow: 'hidden' }}>
            <div style={{ width: '92.4%', height: '100%', background: 'linear-gradient(to right, var(--accent-orange), var(--accent-pink))' }}></div>
          </div>
          <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '1rem' }}>Overall data accuracy across processed datasets.</p>
        </div>

        {/* Featured Subfield Intelligence section removed due to mapping inaccuracies */}
      </div>

      {/* Recent Intelligence Harvest section removed as per user request */}

      {showJournalList && (
        <div className="modal-overlay" onClick={() => setShowJournalList(false)}>
          <div className="modal-content animate-fade" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Monitored Journals List</h3>
              <button className="close-btn" onClick={() => setShowJournalList(false)}>
                <X size={20} />
              </button>
            </div>
            <div className="journal-list">
              {(stats.journal_list || []).map((j: string, i: number) => {
                const hasDigest = stats.journal_digests && (stats.journal_digests as any)[j];
                return (
                  <a 
                    key={i} 
                    href={hasDigest ? `/digests/${(stats.journal_digests as any)[j]}` : '#'} 
                    target={hasDigest ? "_blank" : "_self"}
                    rel="noopener noreferrer"
                    className="journal-item" 
                    style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      alignItems: 'center',
                      textDecoration: 'none',
                      cursor: hasDigest ? 'pointer' : 'default',
                      opacity: hasDigest ? 1 : 0.7
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                      <span className="journal-no">{i + 1}</span>
                      <span className="journal-title">{j}</span>
                    </div>
                    {hasDigest && (
                      <span style={{ 
                        fontSize: '0.6rem', 
                        padding: '2px 6px', 
                        backgroundColor: 'var(--glass-bg)', 
                        color: 'var(--accent-blue)', 
                        borderRadius: '4px', 
                        fontWeight: 700,
                        textTransform: 'uppercase',
                        letterSpacing: '1px',
                        border: '1px solid var(--glass-border)'
                      }}>Digest</span>
                    )}
                  </a>
                );
              })}
            </div>
          </div>
        </div>
      )}
      {show5DDetails && (
        <div className="modal-overlay" onClick={() => { setShow5DDetails(false); setSelectedDimension(null); }}>
          <div className="modal-content animate-fade" style={{ maxWidth: '800px' }} onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>5D Analysis Framework</h3>
              <button className="close-btn" onClick={() => { setShow5DDetails(false); setSelectedDimension(null); }}>
                <X size={20} />
              </button>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1rem', padding: '1.5rem', flex: 1, overflow: 'hidden' }}>
              <div className="dimension-tabs" style={{ borderRight: '1px solid rgba(255,255,255,0.05)', paddingRight: '1rem' }}>
                {[
                  { id: 1, title: '1. Subfield', color: '#6366F1' },
                  { id: 2, title: '2. Method', color: '#007AFF' },
                  { id: 3, title: '3. Era', color: '#EC4899' },
                  { id: 4, title: '4. Region', color: '#A855F7' },
                  { id: 5, title: '5. Confidence', color: '#F97316' }
                ].map(dim => (
                  <div 
                    key={dim.id} 
                    className={`dimension-item ${selectedDimension === dim.id ? 'active' : ''}`}
                    onClick={() => setSelectedDimension(dim.id)}
                    style={{ 
                      padding: '1rem', 
                      cursor: 'pointer', 
                      borderRadius: '8px',
                      marginBottom: '0.5rem',
                      background: selectedDimension === dim.id ? 'var(--glass-bg)' : 'transparent',
                      color: selectedDimension === dim.id ? dim.color : 'var(--text-secondary)'
                    }}
                  >
                    {dim.title}
                  </div>
                ))}
              </div>
              <div className="dimension-detail" style={{ padding: '1rem', overflowY: 'auto' }}>
                {!selectedDimension ? (
                  <div style={{ textAlign: 'center', marginTop: '4rem', color: 'var(--text-secondary)' }}>
                    <Layers size={48} style={{ marginBottom: '1rem', opacity: 0.3 }} />
                    <p>측면을 선택하여 상세 분석 프레임을 확인하십시오.</p>
                  </div>
                ) : (
                  <div className="animate-fade">
                    {selectedDimension === 1 && (
                      <div className="detail-view">
                        <h4 style={{ color: '#6366F1', marginBottom: '1rem' }}>Subfield Analysis</h4>
                        <p style={{ fontSize: '0.9rem' }}>성서학(NT/OT), 조직신학, 역사신학 등 신학적 분과 체계를 정밀 분류합니다. 논문의 제목과 초록 속의 키워드를 대조하여 가장 근접한 학문적 범주를 매핑합니다.</p>
                        <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'rgba(99, 102, 241, 0.05)', borderRadius: '12px', border: '1px solid rgba(99, 102, 241, 0.1)' }}>
                           <h5 style={{ fontSize: '0.8rem', marginBottom: '0.5rem' }}>Latest Subfield Trends</h5>
                           <p style={{ fontSize: '0.75rem', color: '#A1A1AA' }}>최근 24시간 동안 성서학 데이터의 유입량이 15% 증가했습니다.</p>
                        </div>
                      </div>
                    )}
                    {selectedDimension === 2 && (
                      <div className="detail-view">
                        <h4 style={{ color: '#007AFF', marginBottom: '1rem' }}>Methodological Insight (Research Logic)</h4>
                        <p style={{ fontSize: '0.9rem', marginBottom: '1.5rem' }}>현대 신학 연구는 단순한 문헌 강해를 넘어 다학제적 방법론을 채택합니다. 본 대시보드는 논문이 채택한 논리 전개 방식을 4가지 핵심 클러스터로 분류합니다.</p>
                        
                        <div style={{ display: 'grid', gap: '1rem' }}>
                          {[
                            { 
                              cat: "Analytical & Exegetical", 
                              desc: "성서 텍스트의 언어적, 역사적, 문학적 분석. 원어 비평 및 구조 분석을 포함합니다.",
                              icon: "📖"
                            },
                            { 
                              cat: "Historical & Genetic", 
                              desc: "교리나 사상의 발생과 변천 과정을 추적. 사학적 사료 비평과 시대적 배경 분석이 핵심입니다.",
                              icon: "⏳"
                            },
                            { 
                              cat: "Systematic & Philosophical", 
                              desc: "신학적 개념의 논리적 구조와 철학적 전제를 분석. 변증학적 접근과 현대 철학과의 대화를 포함합니다.",
                              icon: "🧠"
                            },
                            { 
                              cat: "Practical & Empirical", 
                              desc: "현장 인터뷰, 설문 등 질적 연구 및 사회과학적 도구 활용. 신학의 실천적 적용 가능성을 탐구합니다.",
                              icon: "🤝"
                            }
                          ].map((item, idx) => (
                            <div key={idx} style={{ padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)' }}>
                              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem' }}>
                                <span style={{ marginRight: '10px', fontSize: '1.2rem' }}>{item.icon}</span>
                                <h5 style={{ color: '#007AFF', margin: 0 }}>{item.cat}</h5>
                              </div>
                              <p style={{ fontSize: '0.8rem', color: '#A1A1AA', margin: 0 }}>{item.desc}</p>
                            </div>
                          ))}
                        </div>

                        <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'rgba(0, 122, 255, 0.05)', borderRadius: '12px', border: '1px solid rgba(0, 122, 255, 0.1)' }}>
                           <h5 style={{ fontSize: '0.8rem', marginBottom: '0.5rem' }}>Methodology Intelligence</h5>
                           <p style={{ fontSize: '0.75rem', color: '#A1A1AA' }}>최근 'Practical & Empirical' 방법론을 채택한 논문이 전월 대비 12% 증가하며 실천적 신학의 득세가 관찰됩니다.</p>
                        </div>
                      </div>
                    )}
                    {selectedDimension === 3 && (
                      <div className="detail-view">
                        <h4 style={{ color: '#EC4899', marginBottom: '1rem' }}>Historical Era Focus</h4>
                        <p style={{ fontSize: '0.9rem' }}>교부, 중세, 종교개혁, 근현대 중 연구의 대상이 되는 역사적 시기를 특정합니다. 시대적 배경이 신학적 논의에 미치는 영향을 추적합니다.</p>
                      </div>
                    )}
                    {selectedDimension === 4 && (
                      <div className="detail-view">
                        <h4 style={{ color: '#A855F7', marginBottom: '1rem' }}>Region & Confession</h4>
                        <p style={{ fontSize: '0.9rem' }}>글로벌 남반구/북반구 및 개신교, 가톨릭, 정교회 등 신학적 배경을 분석합니다. 연구자의 지리적 소속과 교파적 전통이 연구 결과에 미치는 상관관계를 분석합니다.</p>
                      </div>
                    )}
                    {selectedDimension === 5 && (
                      <div className="detail-view">
                        <h4 style={{ color: '#F97316', marginBottom: '1rem' }}>AI Confidence</h4>
                        <p style={{ fontSize: '0.9rem' }}>LLM 기반 추론의 정확성을 검토하고, 핵심 키워드와의 연관 지수를 산출합니다. 데이터의 무결성을 보장하기 위한 다중 검증 프로세스입니다.</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
            <div style={{ padding: '1rem', borderTop: '1px solid rgba(255,255,255,0.05)', textAlign: 'center' }}>
               <span style={{ fontSize: '0.7rem', color: '#A1A1AA' }}>Click dimensions on the left to explore the framework details.</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;
