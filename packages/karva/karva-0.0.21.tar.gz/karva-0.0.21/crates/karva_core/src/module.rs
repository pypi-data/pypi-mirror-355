use std::{
    collections::HashSet,
    fmt::{self, Display},
    hash::{Hash, Hasher},
};

use karva_project::{path::SystemPathBuf, project::Project, utils::module_name};
use ruff_text_size::TextSize;

use crate::{
    case::TestCase,
    discovery::visitor::source_text,
    fixture::{Fixture, HasFixtures},
    utils::from_text_size,
};

/// The type of module.
/// This is used to differentiation between files that contain only test functions and files that contain only configuration functions.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ModuleType {
    Test,
    Configuration,
}

impl ModuleType {
    #[must_use]
    pub fn from_path(path: &SystemPathBuf) -> Self {
        if path.file_name() == Some("conftest.py") {
            Self::Configuration
        } else {
            Self::Test
        }
    }
}

/// A module represents a single python file.
pub struct Module<'proj> {
    pub path: SystemPathBuf,
    pub project: &'proj Project,
    test_cases: Vec<TestCase>,
    fixtures: Vec<Fixture>,
    pub module_type: ModuleType,
}

impl<'proj> Module<'proj> {
    #[must_use]
    pub fn new(
        project: &'proj Project,
        path: &SystemPathBuf,
        test_cases: Vec<TestCase>,
        fixtures: Vec<Fixture>,
        module_type: ModuleType,
    ) -> Self {
        Self {
            path: path.clone(),
            project,
            test_cases,
            fixtures,
            module_type,
        }
    }

    #[must_use]
    pub const fn path(&self) -> &SystemPathBuf {
        &self.path
    }

    #[must_use]
    pub fn name(&self) -> String {
        module_name(self.project.cwd(), &self.path)
    }

    #[must_use]
    pub fn test_cases(&self) -> Vec<&TestCase> {
        self.test_cases.iter().collect()
    }

    #[must_use]
    pub fn total_test_cases(&self) -> usize {
        self.test_cases.len()
    }

    #[must_use]
    pub fn to_column_row(&self, position: TextSize) -> (usize, usize) {
        let source_text = source_text(&self.path);
        from_text_size(position, &source_text)
    }

    #[must_use]
    pub fn source_text(&self) -> String {
        source_text(&self.path)
    }

    // Optimized method that returns both position and source text in one operation
    #[must_use]
    pub fn to_column_row_with_source(&self, position: TextSize) -> ((usize, usize), String) {
        let source_text = source_text(&self.path);
        let position = from_text_size(position, &source_text);
        (position, source_text)
    }

    pub fn update(&mut self, module: Self) {
        if self.path == module.path {
            for test_case in module.test_cases {
                if !self
                    .test_cases
                    .iter()
                    .any(|existing| existing.name() == test_case.name())
                {
                    self.test_cases.push(test_case);
                }
            }

            for fixture in module.fixtures {
                if !self
                    .fixtures
                    .iter()
                    .any(|existing| existing.name() == fixture.name())
                {
                    self.fixtures.push(fixture);
                }
            }
        }
    }

    #[must_use]
    pub fn uses_fixture(&self, fixture_name: &str) -> bool {
        self.test_cases
            .iter()
            .any(|tc| tc.uses_fixture(fixture_name))
    }

    #[must_use]
    pub fn is_empty(&self) -> bool {
        self.test_cases.is_empty() && self.fixtures.is_empty()
    }
}

impl<'proj> HasFixtures<'proj> for Module<'proj> {
    fn all_fixtures<'a: 'proj>(&'a self, test_cases: Option<&[&TestCase]>) -> Vec<&'proj Fixture> {
        self.fixtures
            .iter()
            .filter(|f| {
                test_cases
                    .is_none_or(|test_cases| test_cases.iter().any(|tc| tc.uses_fixture(f.name())))
            })
            .collect()
    }
}

impl fmt::Debug for Module<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("Module")
            .field("file", &self.path)
            .field("functions", &self.test_cases)
            .finish()
    }
}

impl Display for Module<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.name())
    }
}

impl Hash for Module<'_> {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.path.hash(state);
    }
}

impl PartialEq for Module<'_> {
    fn eq(&self, other: &Self) -> bool {
        self.path == other.path && self.name() == other.name()
    }
}

impl Eq for Module<'_> {}

#[derive(Debug, PartialEq, Eq)]
pub struct StringModule {
    pub test_cases: HashSet<String>,
    pub fixtures: HashSet<(String, String)>,
}

impl From<&Module<'_>> for StringModule {
    fn from(module: &Module<'_>) -> Self {
        Self {
            test_cases: module.test_cases().iter().map(|tc| tc.name()).collect(),
            fixtures: module
                .all_fixtures(None)
                .iter()
                .map(|f| (f.name().to_string(), f.scope().to_string()))
                .collect(),
        }
    }
}
